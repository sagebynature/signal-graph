from __future__ import annotations

from signal_graph.models.source import RawSourceItem


class PremiumStubConnector:
    def fetch(self, **kwargs: str) -> list[RawSourceItem]:
        return []
