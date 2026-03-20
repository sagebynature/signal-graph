from __future__ import annotations

import json

import typer

from signal_graph.config import DEFAULT_PROJECT_DIR
from signal_graph.connectors.base import BaseConnector
from signal_graph.connectors.public_web import PublicWebConnector
from signal_graph.services.raw_items import persist_raw_items
from signal_graph.storage.sqlite import SqliteStore

_PREMIUM_FETCH_UNAVAILABLE_MESSAGE = "premium fetch is not implemented in this build."


def _get_connector(source: str) -> BaseConnector:
    if source == "web":
        return PublicWebConnector()
    raise typer.BadParameter(f"unsupported source: {source}")


def fetch(
    source: str = typer.Option(..., "--source"),
    query: str = typer.Option(..., "--query"),
) -> None:
    if source == "premium":
        typer.echo(_PREMIUM_FETCH_UNAVAILABLE_MESSAGE)
        raise typer.Exit(code=1)

    connector = _get_connector(source)
    raw_items = connector.fetch(query=query)
    store = SqliteStore(DEFAULT_PROJECT_DIR / "signal_graph.db")
    persisted_items = persist_raw_items(store, raw_items)
    print(
        json.dumps([raw_item.model_dump(mode="json") for raw_item in persisted_items])
    )
