from __future__ import annotations

from hashlib import sha256

from signal_graph.models.source import RawSourceItem


class PublicWebConnector:
    def fetch(self, **kwargs: str) -> list[RawSourceItem]:
        query = kwargs["query"]
        query_hash = sha256(query.encode()).hexdigest()[:12]
        return [
            RawSourceItem(
                raw_item_id=f"raw-web-{query_hash}",
                source_tier="tier2_public",
                source_name="public_web",
                source_url=f"https://example.com/search?q={query.replace(' ', '+')}",
                raw_text=f"Public web result for {query}",
                raw_payload=query,
            )
        ]
