from __future__ import annotations

from pathlib import Path

import typer

from signal_graph.config import DEFAULT_PROJECT_DIR
from signal_graph.services.research import (
    build_and_persist_research_bundle,
    load_research_bundle_input,
)
from signal_graph.storage.sqlite import SqliteStore


def research(
    event_candidate: str = typer.Option(..., "--event-candidate"),
    bundle_file: Path | None = typer.Option(None, "--bundle-file"),
    allow_empty: bool = typer.Option(False, "--allow-empty"),
) -> None:
    store = SqliteStore(DEFAULT_PROJECT_DIR / "signal_graph.db")
    try:
        bundle_input = load_research_bundle_input(bundle_file)
        bundle = build_and_persist_research_bundle(
            store,
            event_candidate,
            bundle_input=bundle_input,
            allow_empty=allow_empty,
        )
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc
    print(bundle.model_dump_json())
