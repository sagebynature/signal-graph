from __future__ import annotations

from pathlib import Path

import typer

from signal_graph.config import DEFAULT_PROJECT_DIR
from signal_graph.services.journal import (
    create_journal_signal,
    parse_intent_status,
    parse_optional_datetime,
    parse_origin_type,
    persist_journal_signal,
)
from signal_graph.storage.sqlite import SqliteStore


def capture_signal(
    text: str = typer.Option(..., "--text", help="Raw signal text to capture."),
    origin_type: str = typer.Option(
        "user",
        "--origin-type",
        help="Signal origin type: user, agent_artifact, or external_reference.",
    ),
    source_name: str = typer.Option(
        "manual",
        "--source-name",
        help="Short source name for the captured signal.",
    ),
    source_url: str | None = typer.Option(None, "--source-url"),
    source_ref: str | None = typer.Option(None, "--source-ref"),
    raw_payload: str | None = typer.Option(None, "--raw-payload"),
    observed_at: str | None = typer.Option(None, "--observed-at"),
    published_at: str | None = typer.Option(None, "--published-at"),
    host: str | None = typer.Option(None, "--host"),
    process: str | None = typer.Option(None, "--process"),
    runtime_family: str | None = typer.Option(None, "--runtime-family"),
    session_id: str | None = typer.Option(None, "--session-id"),
    role: str | None = typer.Option(None, "--role"),
    workspace_path: str | None = typer.Option(
        None,
        "--workspace-path",
        help="Workspace path associated with the signal.",
    ),
    intent_status: str = typer.Option("unknown", "--intent-status"),
    why: str | None = typer.Option(None, "--why"),
    who: list[str] | None = typer.Option(None, "--who"),
    what: list[str] | None = typer.Option(None, "--what"),
    where: list[str] | None = typer.Option(None, "--where"),
    how: list[str] | None = typer.Option(None, "--how"),
) -> None:
    signal = create_journal_signal(
        text=text,
        origin_type=parse_origin_type(origin_type),
        source_name=source_name,
        source_url=source_url,
        source_ref=source_ref,
        raw_payload=raw_payload,
        observed_at=parse_optional_datetime(observed_at),
        published_at=parse_optional_datetime(published_at),
        agent_host=host,
        agent_process=process,
        agent_runtime=runtime_family,
        agent_session_id=session_id,
        agent_role=role,
        workspace_path=workspace_path or str(Path.cwd()),
        intent_status=parse_intent_status(intent_status),
        why_text=why,
        who_refs=who or [],
        what_refs=what or [],
        where_refs=where or [],
        how_refs=how or [],
    )
    store = SqliteStore(DEFAULT_PROJECT_DIR / "signal_graph.db")
    persisted = persist_journal_signal(store, signal)
    print(persisted.model_dump_json())
