from __future__ import annotations


def install_fake_journal_graph_client(monkeypatch) -> None:
    class FakeGraphClient:
        def run(self, _query: str, _params: dict | None = None) -> list[dict]:
            return []

        def run_in_transaction(
            self, statements: list[tuple[str, dict | None]]
        ) -> list[list[dict]]:
            return [
                [{"signal_id": (statement[1] or {})["signal_id"]}]
                for statement in statements
            ]

        def close(self) -> None:
            return None

    monkeypatch.setattr("signal_graph.services.journal.GraphClient", FakeGraphClient)
