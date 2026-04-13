from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from signal_graph.memory_v2.models import (
    Actor,
    ArtifactShare,
    Correction,
    DerivedInterpretation,
    MemoryEvent,
    Owner,
    Redaction,
)


class FileMemoryStore:
    def __init__(self, root: Path):
        self.root = root
        self._owners: dict[str, Owner] = {}
        self._owners_by_email: dict[str, str] = {}
        self._actors: dict[str, Actor] = {}
        self._events: dict[str, MemoryEvent] = {}
        self._artifacts: dict[str, ArtifactShare] = {}
        self._derived: dict[str, DerivedInterpretation] = {}
        self._corrections: dict[str, Correction] = {}
        self._redactions: dict[str, Redaction] = {}
        self._ensure_layout()

    def describe_layout(self) -> dict[str, str]:
        self._ensure_layout()
        return {
            "root": str(self.root),
            "owners": str(self.root / "owners"),
            "actors": str(self.root / "actors"),
            "events": str(self.root / "events"),
            "artifacts_raw": str(self.root / "artifacts" / "raw"),
            "artifacts_meta": str(self.root / "artifacts" / "shares"),
            "derived": str(self.root / "derived"),
            "corrections": str(self.root / "corrections"),
            "redactions": str(self.root / "redactions"),
            "views_markdown": str(self.root / "views" / "markdown"),
        }

    def save_owner(self, owner: Owner) -> Owner:
        self._owners[owner.owner_id] = owner
        self._owners_by_email[owner.email] = owner.owner_id
        self._write_json("owners", owner.owner_id, owner.model_dump(mode="json"))
        return owner

    def get_owner(self, owner_id: str) -> Owner | None:
        return self._owners.get(owner_id)

    def get_owner_by_email(self, email: str) -> Owner | None:
        owner_id = self._owners_by_email.get(email)
        if owner_id is None:
            return None
        return self._owners[owner_id]

    def save_actor(self, actor: Actor) -> Actor:
        self._actors[actor.actor_id] = actor
        self._write_json("actors", actor.actor_id, actor.model_dump(mode="json"))
        return actor

    def get_actor(self, actor_id: str) -> Actor | None:
        return self._actors.get(actor_id)

    def save_event(self, event: MemoryEvent) -> MemoryEvent:
        self._events[event.event_id] = event
        self._write_json("events", event.event_id, event.model_dump(mode="json"))
        return event

    def get_event(self, event_id: str) -> MemoryEvent | None:
        return self._events.get(event_id)

    def list_events(self) -> list[MemoryEvent]:
        return list(self._events.values())

    def save_artifact(self, artifact: ArtifactShare) -> ArtifactShare:
        self._artifacts[artifact.artifact_id] = artifact
        self._write_json(
            "artifacts/shares", artifact.artifact_id, artifact.model_dump(mode="json")
        )
        return artifact

    def get_artifact(self, artifact_id: str) -> ArtifactShare | None:
        return self._artifacts.get(artifact_id)

    def list_artifacts(self) -> list[ArtifactShare]:
        return list(self._artifacts.values())

    def save_derived(
        self, interpretation: DerivedInterpretation
    ) -> DerivedInterpretation:
        self._derived[interpretation.interpretation_id] = interpretation
        self._write_json(
            "derived",
            interpretation.interpretation_id,
            interpretation.model_dump(mode="json"),
        )
        return interpretation

    def list_derived(self) -> list[DerivedInterpretation]:
        return list(self._derived.values())

    def save_correction(self, correction: Correction) -> Correction:
        self._corrections[correction.correction_id] = correction
        self._write_json(
            "corrections",
            correction.correction_id,
            correction.model_dump(mode="json"),
        )
        return correction

    def list_corrections(self) -> list[Correction]:
        return list(self._corrections.values())

    def save_redaction(self, redaction: Redaction) -> Redaction:
        self._redactions[redaction.redaction_id] = redaction
        self._write_json(
            "redactions",
            redaction.redaction_id,
            redaction.model_dump(mode="json"),
        )
        return redaction

    def list_redactions(self) -> list[Redaction]:
        return list(self._redactions.values())

    def copy_artifact(self, source_path: Path, artifact_id: str) -> tuple[str, str]:
        raw_dir = self.root / "artifacts" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        target = raw_dir / f"{artifact_id}-{source_path.name}"
        shutil.copy2(source_path, target)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        return str(target), digest

    def write_markdown_view(self, stem: str, text: str) -> str:
        view_dir = self.root / "views" / "markdown"
        view_dir.mkdir(parents=True, exist_ok=True)
        path = view_dir / f"{stem}.md"
        path.write_text(text)
        return str(path)

    def _ensure_layout(self) -> None:
        for relative in (
            "owners",
            "actors",
            "events",
            "artifacts/raw",
            "artifacts/shares",
            "derived",
            "corrections",
            "redactions",
            "views/markdown",
        ):
            (self.root / relative).mkdir(parents=True, exist_ok=True)

    def _write_json(self, relative_dir: str, stem: str, payload: dict) -> None:
        directory = self.root / relative_dir
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{stem}.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True)
        )
