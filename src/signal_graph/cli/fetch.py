from __future__ import annotations

import typer

from signal_graph.connectors.base import BaseConnector
from signal_graph.connectors.premium_stub import PremiumStubConnector
from signal_graph.connectors.public_web import PublicWebConnector


def _get_connector(source: str) -> BaseConnector:
    if source == "web":
        return PublicWebConnector()
    if source == "premium":
        return PremiumStubConnector()
    raise typer.BadParameter(f"unsupported source: {source}")


def fetch(
    source: str = typer.Option(..., "--source"),
    query: str = typer.Option(..., "--query"),
) -> None:
    connector = _get_connector(source)
    raw_items = connector.fetch(query=query)
    print([raw_item.model_dump(mode="json") for raw_item in raw_items])
