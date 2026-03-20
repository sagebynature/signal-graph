from __future__ import annotations

import signal_graph.graph.client as client_module


class FakeRecord:
    def __init__(self, payload: dict):
        self._payload = payload

    def data(self) -> dict:
        return self._payload


class FakeSession:
    def __init__(self, calls: list[tuple]):
        self.calls = calls

    def __enter__(self) -> FakeSession:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def run(self, query: str, params: dict) -> list[FakeRecord]:
        self.calls.append(("run", query, params))
        return [FakeRecord({"value": params["value"]})]


class FakeDriver:
    def __init__(self, calls: list[tuple]):
        self.calls = calls

    def verify_connectivity(self) -> None:
        self.calls.append(("verify_connectivity",))

    def session(self, *, database: str) -> FakeSession:
        self.calls.append(("session", database))
        return FakeSession(self.calls)

    def close(self) -> None:
        self.calls.append(("close",))


def test_graph_client_uses_driver_and_executes_query(monkeypatch):
    calls: list[tuple] = []

    class FakeGraphDatabase:
        @staticmethod
        def driver(uri: str, auth: tuple[str, str]) -> FakeDriver:
            calls.append(("driver", uri, auth))
            return FakeDriver(calls)

    monkeypatch.setenv("NEO4J_URI", "neo4j://graph-host:7687")
    monkeypatch.setenv("NEO4J_AUTH", "neo4j/password")
    monkeypatch.setattr(client_module, "GraphDatabase", FakeGraphDatabase)

    client = client_module.GraphClient()
    rows = client.run("RETURN $value AS value", {"value": 7})
    client.close()

    assert rows == [{"value": 7}]
    assert calls == [
        ("driver", "neo4j://graph-host:7687", ("neo4j", "password")),
        ("verify_connectivity",),
        ("session", "neo4j"),
        ("run", "RETURN $value AS value", {"value": 7}),
        ("close",),
    ]
