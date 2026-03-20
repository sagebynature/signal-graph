from __future__ import annotations

import typer

from trade_graph.config import DEFAULT_PROJECT_DIR
from trade_graph.services.research import build_and_persist_research_bundle
from trade_graph.storage.sqlite import SqliteStore


def research(event_candidate: str = typer.Option(..., "--event-candidate")) -> None:
    store = SqliteStore(DEFAULT_PROJECT_DIR / "trade_graph.db")
    bundle = build_and_persist_research_bundle(store, event_candidate)
    print(bundle.model_dump_json())
