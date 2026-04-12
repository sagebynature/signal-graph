from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

from signal_graph.memory_v2.models import (
    Actor,
    ArtifactShare,
    CapturePolicy,
    Correction,
    DerivedInterpretation,
    ExplanationActor,
    ExplanationResponse,
    HookPhase,
    MemoryEvent,
    Owner,
    PendingWhy,
    QueryResult,
    WhyInference,
)
from signal_graph.memory_v2.graph import (
    MemoryGraphBoundary,
    NoOpMemoryGraphBoundary,
    artifact_projection_statements,
    correction_projection_statements,
    event_projection_statements,
)
from signal_graph.memory_v2.store import FileMemoryStore


SUPPORTED_RUNTIMES = {"claude-code", "opencode", "gemini", "codex"}


class MemoryService:
    def __init__(
        self,
        store: FileMemoryStore,
        policy: CapturePolicy,
        graph_boundary: MemoryGraphBoundary | None = None,
    ):
        self.store = store
        self.policy = policy
        self.graph_boundary = graph_boundary or NoOpMemoryGraphBoundary()

    def create_owner(self, *, email: str, display_name: str) -> Owner:
        existing = self.store.get_owner_by_email(email)
        if existing is not None:
            raise ValueError(f"owner with email {email} already exists")
        owner = Owner(
            owner_id=self._new_id("owner"),
            email=email,
            display_name=display_name,
            created_at=self._now(),
        )
        return self.store.save_owner(owner)

    def get_owner_by_email(self, email: str) -> Owner:
        owner = self.store.get_owner_by_email(email)
        if owner is None:
            raise ValueError(f"owner {email} not found")
        return owner

    def register_actor(
        self,
        *,
        owner_email: str,
        runtime_family: str,
        host: str,
        session_id: str,
    ) -> Actor:
        owner = self.store.get_owner_by_email(owner_email)
        if owner is None:
            raise ValueError(
                f"owner {owner_email} must exist before registering actors"
            )
        self._require_runtime(runtime_family)
        actor = Actor(
            actor_id=self._new_id("actor"),
            owner_id=owner.owner_id,
            runtime_family=runtime_family,
            host=host,
            session_id=session_id,
            created_at=self._now(),
        )
        return self.store.save_actor(actor)

    def capture_hook_event(
        self,
        *,
        owner_email: str,
        actor_id: str,
        phase: HookPhase,
        action_text: str,
        observed_facts: list[str],
        topic_refs: list[str],
        occurred_at: datetime,
        parent_event_id: str | None = None,
        inferred_why: str | None = None,
        why_confidence: float | None = None,
        confirmed: bool = False,
        evidence_refs: list[str] | None = None,
    ) -> MemoryEvent:
        owner = self.get_owner_by_email(owner_email)
        actor = self.store.get_actor(actor_id)
        if actor is None:
            raise ValueError(f"actor {actor_id} not found")
        if actor.owner_id != owner.owner_id:
            raise ValueError("actor owner link does not match requested owner")
        why_inference, pending_why = self._resolve_why(
            inferred_why=inferred_why,
            why_confidence=why_confidence,
            confirmed=confirmed,
        )
        event = MemoryEvent(
            event_id=self._new_id("event"),
            owner_id=owner.owner_id,
            actor_id=actor.actor_id,
            runtime_family=actor.runtime_family,
            host=actor.host,
            session_id=actor.session_id,
            phase=phase,
            action_text=action_text,
            observed_facts=observed_facts
            if self.policy.auto_capture_observable_facts
            else [],
            topic_refs=topic_refs,
            parent_event_id=parent_event_id,
            evidence_refs=evidence_refs or [],
            why_inference=why_inference,
            pending_why=pending_why,
            occurred_at=occurred_at,
            created_at=self._now(),
        )
        saved = self.store.save_event(event)
        self.graph_boundary.project(
            event_projection_statements(owner=owner, actor=actor, event=saved)
        )
        return saved

    def share_artifact(
        self,
        *,
        owner_email: str,
        actor_id: str,
        source_path: Path,
        title: str,
        topic_refs: list[str],
        occurred_at: datetime,
    ) -> ArtifactShare:
        owner = self.get_owner_by_email(owner_email)
        actor = self.store.get_actor(actor_id)
        if actor is None:
            raise ValueError(f"actor {actor_id} not found")
        if actor.owner_id != owner.owner_id:
            raise ValueError("actor owner link does not match requested owner")
        artifact_id = self._new_id("artifact")
        canonical_raw_path, sha256 = self.store.copy_artifact(source_path, artifact_id)
        share_event = self.capture_hook_event(
            owner_email=owner_email,
            actor_id=actor_id,
            phase="share_artifact",
            action_text=f"Shared artifact: {title}",
            observed_facts=[f"shared {source_path.name}"],
            topic_refs=topic_refs,
            occurred_at=occurred_at,
            evidence_refs=[canonical_raw_path],
        )
        artifact = ArtifactShare(
            artifact_id=artifact_id,
            owner_id=owner.owner_id,
            actor_id=actor.actor_id,
            title=title,
            source_path=str(source_path),
            canonical_raw_path=canonical_raw_path,
            sha256=sha256,
            topic_refs=topic_refs,
            share_event_id=share_event.event_id,
            shared_at=occurred_at,
        )
        saved = self.store.save_artifact(artifact)
        share_event = self.store.get_event(saved.share_event_id)
        if share_event is None:
            raise ValueError(f"share event {saved.share_event_id} not found")
        self.graph_boundary.project(
            artifact_projection_statements(
                owner=owner, event=share_event, artifact=saved
            )
        )
        return saved

    def derive_artifact_memory(
        self,
        *,
        owner_email: str,
        artifact_id: str,
        source_event_id: str,
        summary: str,
        topics: list[str],
        confidence: float,
    ) -> DerivedInterpretation:
        owner = self.get_owner_by_email(owner_email)
        artifact = self.store.get_artifact(artifact_id)
        if artifact is None:
            raise ValueError(f"artifact {artifact_id} not found")
        markdown_view_path = self.store.write_markdown_view(
            self._new_id("view"),
            "\n".join(
                [
                    f"# Derived interpretation for {artifact.title}",
                    "",
                    summary,
                    "",
                    f"Topics: {', '.join(topics)}",
                    f"Confidence: {confidence:.2f}",
                ]
            ),
        )
        interpretation = DerivedInterpretation(
            interpretation_id=self._new_id("derived"),
            owner_id=owner.owner_id,
            artifact_id=artifact_id,
            source_event_id=source_event_id,
            summary=summary,
            topics=topics,
            confidence=confidence,
            markdown_view_path=markdown_view_path,
            created_at=self._now(),
        )
        return self.store.save_derived(interpretation)

    def record_correction(
        self,
        *,
        owner_email: str,
        target_id: str,
        instruction: str,
        topic: str | None = None,
    ) -> Correction:
        owner = self.get_owner_by_email(owner_email)
        for existing in self.store.list_corrections():
            if (
                existing.owner_id == owner.owner_id
                and existing.target_id == target_id
                and existing.topic == topic
                and existing.instruction == instruction
            ):
                return existing
        correction = Correction(
            correction_id=self._new_id("correction"),
            owner_id=owner.owner_id,
            target_id=target_id,
            topic=topic,
            instruction=instruction,
            created_at=self._now(),
        )
        saved = self.store.save_correction(correction)
        self.graph_boundary.project(
            correction_projection_statements(owner=owner, correction=saved)
        )
        return saved

    def query(
        self,
        *,
        owner_email: str,
        topic: str | None = None,
        on_date: date | None = None,
    ) -> QueryResult:
        owner = self.get_owner_by_email(owner_email)
        events = [
            event
            for event in self.store.list_events()
            if event.owner_id == owner.owner_id
            and self._event_matches(event, topic, on_date)
        ]
        artifacts = [
            artifact
            for artifact in self.store.list_artifacts()
            if artifact.owner_id == owner.owner_id
            and self._topic_matches(artifact.topic_refs, topic)
        ]
        corrections = self._matching_corrections(owner.owner_id, topic=topic)
        derived = [
            item
            for item in self.store.list_derived()
            if item.owner_id == owner.owner_id
            and self._topic_matches(item.topics, topic)
            and not self._is_corrected(item.interpretation_id, item.topics, corrections)
        ]
        return QueryResult(
            owner=owner,
            topic=topic,
            on_date=on_date,
            events=sorted(events, key=lambda event: event.occurred_at),
            artifacts=sorted(artifacts, key=lambda artifact: artifact.shared_at),
            derived_interpretations=sorted(derived, key=lambda item: item.created_at),
            guidance=[correction.instruction for correction in corrections],
            applied_corrections=corrections,
        )

    def explain_action(self, event_id: str) -> ExplanationResponse:
        event = self.store.get_event(event_id)
        if event is None:
            raise ValueError(f"event {event_id} not found")
        owner = self.store.get_owner(event.owner_id)
        actor = self.store.get_actor(event.actor_id)
        if owner is None or actor is None:
            raise ValueError("event owner/actor linkage is incomplete")
        corrections = self._matching_corrections(
            owner.owner_id,
            topic=event.topic_refs[0] if event.topic_refs else None,
            target_id=event.event_id,
        )
        return ExplanationResponse(
            owner=owner,
            actor=ExplanationActor(
                actor_id=actor.actor_id,
                runtime_family=actor.runtime_family,
                host=actor.host,
                session_id=actor.session_id,
            ),
            action_text=event.action_text,
            provenance_chain=self._build_provenance_chain(event),
            evidence_refs=event.evidence_refs,
            why_inference=event.why_inference,
            active_corrections=corrections,
            guidance=[correction.instruction for correction in corrections],
        )

    def explain_action_for_owner(
        self, *, owner_email: str, event_id: str
    ) -> ExplanationResponse:
        explanation = self.explain_action(event_id)
        if explanation.owner.email != owner_email:
            raise ValueError("owner scope does not match event owner")
        return explanation

    def _build_provenance_chain(self, event: MemoryEvent) -> list[str]:
        chain: list[str] = []
        current = event
        while current.parent_event_id is not None:
            parent = self.store.get_event(current.parent_event_id)
            if parent is None:
                break
            chain.append(parent.event_id)
            current = parent
        chain.reverse()
        chain.append(event.event_id)
        return chain

    def _resolve_why(
        self,
        *,
        inferred_why: str | None,
        why_confidence: float | None,
        confirmed: bool,
    ) -> tuple[WhyInference | None, PendingWhy | None]:
        if inferred_why is None:
            return None, None
        confidence = why_confidence if why_confidence is not None else 1.0
        if self.policy.require_confirmation_for_inferred_why and not confirmed:
            return None, PendingWhy(
                text=inferred_why,
                confidence=confidence,
                reason="confirmation_required",
            )
        return WhyInference(text=inferred_why, confidence=confidence), None

    def _matching_corrections(
        self,
        owner_id: str,
        *,
        topic: str | None = None,
        target_id: str | None = None,
    ) -> list[Correction]:
        return [
            correction
            for correction in sorted(
                self.store.list_corrections(),
                key=lambda item: item.created_at,
            )
            if correction.owner_id == owner_id
            and (
                (target_id is not None and correction.target_id == target_id)
                or (topic is not None and correction.topic == topic)
            )
        ]

    @staticmethod
    def _is_corrected(
        interpretation_id: str,
        topics: list[str],
        corrections: list[Correction],
    ) -> bool:
        return any(
            correction.target_id == interpretation_id
            or (correction.topic is not None and correction.topic in topics)
            for correction in corrections
        )

    @staticmethod
    def _topic_matches(topic_refs: list[str], topic: str | None) -> bool:
        return topic is None or topic in topic_refs

    @classmethod
    def _event_matches(
        cls,
        event: MemoryEvent,
        topic: str | None,
        on_date: date | None,
    ) -> bool:
        if not cls._topic_matches(event.topic_refs, topic):
            return False
        if on_date is not None and event.occurred_at.date() != on_date:
            return False
        return True

    @staticmethod
    def _require_runtime(runtime_family: str) -> None:
        if runtime_family not in SUPPORTED_RUNTIMES:
            raise ValueError(
                f"runtime_family must be one of {sorted(SUPPORTED_RUNTIMES)}"
            )

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}-{uuid4().hex[:12]}"

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)
