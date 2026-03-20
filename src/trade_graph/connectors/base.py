from __future__ import annotations

from typing import Protocol

from trade_graph.models.source import RawSourceItem


class BaseConnector(Protocol):
    def fetch(self, **kwargs: str) -> list[RawSourceItem]: ...
