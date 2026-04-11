from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import cast
from uuid import uuid4

from signal_graph.graph.client import GraphClient
from signal_graph.graph.schema import JOURNAL_SCHEMA_CONSTRAINTS, journal_signal_statements
from signal_graph.models.journal import (
    IntentStatus,
    JournalSignal,
    MINIMUM_PROVENANCE_FIELDS,
    NON_SEMANTIC_DETERMINISM_FIELDS,
    OriginType,
    RecallArtifact,
)
from signal_graph.storage.sqlite import SqliteStore


def create_journal_signal(
    *,
    text: str,
    origin_type: OriginType,
    source_name: str,
    source_url: str | None = None,
    source_ref: str | None = None,
    raw_payload: str | None = None,
    observed_at: datetime | None = None,
    published_at: datetime | None = None,
    agent_host: str | None = None,
    agent_process: str | None = None,
    agent_runtime: str | None = None,
    agent_session_id: str | None = None,
    agent_role: str | None = None,
    workspace_path: str | None = None,
    intent_status: IntentStatus = "unknown",
    why_text: str | None = None,
    who_refs: list[str] | None = None,
    what_refs: list[str] | None = None,
    where_refs: list[str] | None = None,
    how_refs: list[str] | None = None,
) -> JournalSignal:
    normalized_text = text.strip()
    if not normalized_text:
        raise ValueError("signal text must be non-empty")

    normalized_why = (why_text or "").strip() or None
    if normalized_why is not None and intent_status == "unknown":
        raise ValueError("`why` requires --intent-status explicit or inferred")
    if intent_status != "unknown" and normalized_why is None:
        raise ValueError("intent-status explicit or inferred requires --why")

    payload_material = raw_payload or ""
    content_hash = sha256(f"{normalized_text}\n{payload_material}".encode()).hexdigest()
    return JournalSignal(
        signal_id=f"sig-{uuid4().hex[:12]}",
        origin_type=origin_type,
        source_name=source_name,
        source_url=source_url,
        source_ref=source_ref,
        raw_text=normalized_text,
        raw_payload=raw_payload,
        content_hash=content_hash,
        captured_at=datetime.now(UTC),
        observed_at=observed_at,
        published_at=published_at,
        agent_host=agent_host,
        agent_process=agent_process,
        agent_runtime=agent_runtime,
        agent_session_id=agent_session_id,
        agent_role=agent_role,
        workspace_path=workspace_path,
        intent_status=intent_status,
        why_text=normalized_why,
        who_refs=_normalize_refs(who_refs),
        what_refs=_normalize_refs(what_refs),
        where_refs=_normalize_refs(where_refs),
        how_refs=_normalize_refs(how_refs),
    )


def persist_journal_signal(
    store: SqliteStore, signal: JournalSignal
) -> JournalSignal:
    store.init_db()
    store.save_journal_signal(signal)
    return signal


def journalize_signal(store: SqliteStore, signal_id: str) -> JournalSignal:
    signal = store.get_journal_signal(signal_id)
    if signal is None:
        raise ValueError(f"journal signal not found: {signal_id}")

    graph_path = build_graph_path(signal)
    journaled_signal = signal.model_copy(
        update={
            "graph_path": graph_path,
            "journaled_at": datetime.now(UTC),
        }
    )

    client = GraphClient()
    try:
        for constraint in JOURNAL_SCHEMA_CONSTRAINTS:
            client.run(constraint)
        client.run_in_transaction(journal_signal_statements(journaled_signal))
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()

    store.save_journal_signal(journaled_signal)
    return journaled_signal


def recall_signals(
    store: SqliteStore,
    *,
    query: str,
    artifact_dir: Path,
    limit: int = 5,
    origin_type: str | None = None,
    session_id: str | None = None,
    runtime_family: str | None = None,
    source_name: str | None = None,
) -> RecallArtifact:
    normalized_query = query.strip()
    if not normalized_query and not any(
        [origin_type, session_id, runtime_family, source_name]
    ):
        raise ValueError("recall query must be non-empty unless filters are provided")

    matches = store.search_journal_signals(
        normalized_query,
        limit=limit,
        origin_type=origin_type,
        session_id=session_id,
        runtime_family=runtime_family,
        source_name=source_name,
    )
    if not matches:
        raise ValueError(
            f"no journal signals matched query: {normalized_query or '<filtered request>'}"
        )

    created_at = datetime.now(UTC)
    artifact_id = f"ra-{uuid4().hex[:12]}"
    markdown_text = render_recall_markdown(
        normalized_query,
        matches,
        origin_type=origin_type,
        session_id=session_id,
        runtime_family=runtime_family,
        source_name=source_name,
    )
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / f"{artifact_id}.md"
    artifact_path.write_text(markdown_text)

    artifact = RecallArtifact(
        artifact_id=artifact_id,
        query=normalized_query,
        signal_ids=[signal.signal_id for signal in matches],
        markdown_text=markdown_text,
        artifact_path=str(artifact_path),
        graph_paths={signal.signal_id: build_graph_path(signal) for signal in matches},
        provenance_contract={
            "required_fields": MINIMUM_PROVENANCE_FIELDS,
            "non_semantic_determinism_fields": NON_SEMANTIC_DETERMINISM_FIELDS,
        },
        created_at=created_at,
    )
    store.save_recall_artifact(artifact)
    return artifact


def build_graph_path(signal: JournalSignal) -> list[str]:
    path = ["SIGNAL", f"ORIGIN:{signal.origin_type.upper()}"]
    if signal.who_refs or signal.agent_session_id or signal.agent_process:
        path.append("WHO")
    if signal.what_refs or signal.raw_text:
        path.append("WHAT")
    if signal.captured_at or signal.observed_at or signal.published_at:
        path.append("WHEN")
    if signal.where_refs or signal.source_ref or signal.source_url or signal.workspace_path:
        path.append("WHERE")
    if signal.why_text:
        path.append(f"WHY:{signal.intent_status.upper()}")
    if signal.how_refs:
        path.append("HOW")
    return path


def render_recall_markdown(
    query: str,
    matches: list[JournalSignal],
    *,
    origin_type: str | None = None,
    session_id: str | None = None,
    runtime_family: str | None = None,
    source_name: str | None = None,
) -> str:
    origin_types = sorted({signal.origin_type for signal in matches})
    sessions = sorted(
        {
            signal.agent_session_id
            for signal in matches
            if signal.agent_session_id is not None
        }
    )
    active_filters = _active_filters(
        origin_type=origin_type,
        session_id=session_id,
        runtime_family=runtime_family,
        source_name=source_name,
    )
    lines = [
        "# Signal Recall",
        "",
        f"- Query: `{query or 'none (filter-only recall)'}`",
        f"- Matched signals: {len(matches)}",
        f"- Origin types: {', '.join(origin_types)}",
        f"- Sessions: {', '.join(sessions) if sessions else 'none recorded'}",
        _filters_markdown_line(active_filters),
        "",
        "## Summary",
        (
            "Signal Graph matched signals with provenance-rich recall. "
            "Every entry below preserves raw signal context plus origin, session, "
            "location, graph path, and intent status."
        ),
        "",
        "## Matches",
    ]
    for signal in matches:
        lines.extend(
            [
                "",
                f"### {signal.signal_id}",
                f"- Origin: `{signal.origin_type}` via `{signal.source_name}`",
                f"- Captured at: `{signal.captured_at.isoformat() if signal.captured_at else 'unknown'}`",
                (
                    "- Agent/session: "
                    f"`{signal.agent_runtime or 'human'}` / "
                    f"`{signal.agent_process or 'n/a'}` / "
                    f"`{signal.agent_session_id or 'n/a'}`"
                ),
                f"- Source ref: `{signal.source_ref or signal.source_url or signal.workspace_path or 'none recorded'}`",
                f"- Graph path: `{' -> '.join(build_graph_path(signal))}`",
                (
                    f"- Intent: `{signal.intent_status}` — "
                    f"{signal.why_text or 'why not asserted'}"
                ),
                f"- Who: {', '.join(signal.who_refs) or 'none'}",
                f"- What: {', '.join(signal.what_refs) or 'none'}",
                f"- Where: {', '.join(signal.where_refs) or 'none'}",
                f"- How: {', '.join(signal.how_refs) or 'none'}",
                "",
                "```text",
                signal.raw_text,
                "```",
            ]
        )
    return "\n".join(lines)


def _normalize_refs(refs: list[str] | None) -> list[str]:
    unique_refs = {ref.strip() for ref in refs or [] if ref.strip()}
    return sorted(unique_refs)


def _active_filters(
    *,
    origin_type: str | None,
    session_id: str | None,
    runtime_family: str | None,
    source_name: str | None,
) -> dict[str, str | None]:
    return {
        "origin_type": origin_type,
        "session_id": session_id,
        "runtime_family": runtime_family,
        "source_name": source_name,
    }


def _filters_markdown_line(active_filters: dict[str, str | None]) -> str:
    rendered_filters = [
        f"{key}={value}" for key, value in active_filters.items() if value is not None
    ]
    return f"- Filters: {', '.join(rendered_filters)}" if rendered_filters else "- Filters: none"


def parse_optional_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid datetime value: {value}") from exc


def parse_intent_status(value: str) -> IntentStatus:
    normalized = value.strip().lower()
    valid_statuses = {"explicit", "inferred", "unknown"}
    if normalized not in valid_statuses:
        raise ValueError(
            "intent-status must be one of: explicit, inferred, unknown"
        )
    return cast(IntentStatus, normalized)


def parse_origin_type(value: str) -> OriginType:
    normalized = value.strip().lower()
    valid_origin_types = {"user", "agent_artifact", "external_reference"}
    if normalized not in valid_origin_types:
        raise ValueError(
            "origin-type must be one of: user, agent_artifact, external_reference"
        )
    return cast(OriginType, normalized)
