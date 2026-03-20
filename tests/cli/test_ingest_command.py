from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from neo4j.exceptions import ServiceUnavailable
from typer.testing import CliRunner

from signal_graph.cli.main import app
from signal_graph.graph.schema import SCHEMA_CONSTRAINTS, graph_cleanup_query


def _write_bundle_file(path: Path) -> Path:
    bundle_path = path / "bundle.json"
    bundle_path.write_text(
        json.dumps(
            {
                "supporting_documents": ["https://example.com/nvda-supplier"],
                "contradictions": ["Inventory could cushion the disruption."],
                "entity_resolution_results": {"NVDA": "company:NVDA"},
                "evidence_spans": ["A key supplier reported production delays."],
                "research_confidence": 0.6,
                "research_notes": "Near-term supply tightness could affect shipments.",
            }
        )
    )
    return bundle_path


def _install_fake_graph_client(
    monkeypatch,
    run_calls: list[tuple[str, dict | None]],
    transaction_calls: list[list[tuple[str, dict | None]]],
    *,
    error: Exception | None = None,
) -> None:
    class FakeGraphClient:
        def run(self, query: str, params: dict | None = None) -> list[dict]:
            run_calls.append((query, params))
            return []

        def run_in_transaction(
            self, statements: list[tuple[str, dict | None]]
        ) -> list[list[dict]]:
            transaction_calls.append(list(statements))
            if error is not None:
                raise error
            return [[] for _ in statements]

        def close(self) -> None:
            return None

    monkeypatch.setattr("signal_graph.cli.ingest.GraphClient", FakeGraphClient)


def test_ingest_requires_initialized_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(app, ["ingest", "--event-candidate", "ec-123"])

    assert result.exit_code == 1
    assert result.stdout.strip() == (
        "Project is not initialized. Run `signal-graph init` first."
    )


def test_ingest_reports_graph_connectivity_failures_concisely(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def raise_connectivity_error(*_args, **_kwargs):
        raise ServiceUnavailable("neo4j is unavailable")

    monkeypatch.setattr(
        "signal_graph.cli.ingest._ingest_event_candidate", raise_connectivity_error
    )

    runner = CliRunner()
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["ingest", "--event-candidate", "ec-123"])

    assert result.exit_code == 1
    assert result.stdout.strip() == (
        "Unable to reach the graph database. Check Neo4j settings and try again."
    )


def test_ingest_help_describes_event_candidate_identifier():
    runner = CliRunner()

    result = runner.invoke(app, ["ingest", "--help"])

    assert result.exit_code == 0
    assert "Event candidate id to ingest into the" in result.stdout
    assert "graph." in result.stdout


def test_ingest_creates_graph_event_record(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_calls: list[tuple[str, dict | None]] = []
    transaction_calls: list[list[tuple[str, dict | None]]] = []
    _install_fake_graph_client(monkeypatch, run_calls, transaction_calls)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]
    normalized = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])
    event_candidate_id = json.loads(normalized.stdout)["event_candidate_id"]
    runner.invoke(
        app, ["research", "--event-candidate", event_candidate_id, "--allow-empty"]
    )

    result = runner.invoke(app, ["ingest", "--event-candidate", event_candidate_id])

    assert result.exit_code == 0
    assert "graph_event_id" in result.stdout
    assert [query for query, _ in run_calls] == SCHEMA_CONSTRAINTS
    assert len(transaction_calls) == 1


def test_ingest_persists_graph_event_record(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_calls: list[tuple[str, dict | None]] = []
    transaction_calls: list[list[tuple[str, dict | None]]] = []
    _install_fake_graph_client(monkeypatch, run_calls, transaction_calls)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]
    normalized = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])
    event_candidate_id = json.loads(normalized.stdout)["event_candidate_id"]
    runner.invoke(
        app, ["research", "--event-candidate", event_candidate_id, "--allow-empty"]
    )

    result = runner.invoke(app, ["ingest", "--event-candidate", event_candidate_id])

    assert result.exit_code == 0
    graph_event = json.loads(result.stdout)
    database_path = Path(".signal-graph/signal_graph.db")

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT graph_event_id, event_candidate_id
            FROM graph_events
            WHERE graph_event_id = ?
            """,
            (graph_event["graph_event_id"],),
        ).fetchone()

    assert row == (
        graph_event["graph_event_id"],
        event_candidate_id,
    )
    assert [query for query, _ in run_calls] == SCHEMA_CONSTRAINTS
    assert len(transaction_calls) == 1


def test_ingest_runs_cleanup_and_rebuild_in_one_transaction(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_calls: list[tuple[str, dict | None]] = []
    transaction_calls: list[list[tuple[str, dict | None]]] = []
    _install_fake_graph_client(
        monkeypatch,
        run_calls,
        transaction_calls,
        error=ServiceUnavailable("neo4j is unavailable"),
    )

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]
    normalized = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])
    event_candidate_id = json.loads(normalized.stdout)["event_candidate_id"]
    runner.invoke(
        app, ["research", "--event-candidate", event_candidate_id, "--allow-empty"]
    )

    result = runner.invoke(app, ["ingest", "--event-candidate", event_candidate_id])

    assert result.exit_code == 1
    assert result.stdout.strip() == (
        "Unable to reach the graph database. Check Neo4j settings and try again."
    )
    assert [query for query, _ in run_calls] == SCHEMA_CONSTRAINTS
    assert len(transaction_calls) == 1
    assert len(transaction_calls[0]) == 2


def test_ingest_sends_rich_graph_payload_in_one_transaction(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    run_calls: list[tuple[str, dict | None]] = []
    transaction_calls: list[list[tuple[str, dict | None]]] = []
    _install_fake_graph_client(monkeypatch, run_calls, transaction_calls)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]
    normalized = runner.invoke(
        app,
        [
            "normalize",
            "--raw-item",
            raw_item_id,
            "--event-type",
            "supplier_disruption",
            "--direction",
            "negative",
            "--primary-entity",
            "NVDA",
            "--secondary-entity",
            "SMH",
        ],
    )
    event_candidate_id = json.loads(normalized.stdout)["event_candidate_id"]
    bundle_path = _write_bundle_file(tmp_path)
    runner.invoke(
        app,
        [
            "research",
            "--event-candidate",
            event_candidate_id,
            "--bundle-file",
            str(bundle_path),
        ],
    )

    result = runner.invoke(app, ["ingest", "--event-candidate", event_candidate_id])

    assert result.exit_code == 0
    assert [query for query, _ in run_calls] == SCHEMA_CONSTRAINTS
    assert len(transaction_calls) == 1

    statements = transaction_calls[0]
    assert len(statements) == 2

    cleanup_query, cleanup_params = statements[0]
    graph_query, graph_params = statements[1]

    assert cleanup_query == graph_cleanup_query()
    assert cleanup_params == graph_params
    assert "MERGE (e:Event" in graph_query
    assert "MERGE (rb:ResearchBundle" in graph_query
    assert "HAS_RESEARCH" in graph_query
    assert graph_params == {
        "event_candidate_id": event_candidate_id,
        "title": "NVDA supplier disruption",
        "event_type": "supplier_disruption",
        "direction": "negative",
        "primary_entities": ["NVDA"],
        "secondary_entities": ["SMH"],
        "source_item_ids": [raw_item_id],
        "research_bundle_id": f"rb-{event_candidate_id}",
        "supporting_documents": ["https://example.com/nvda-supplier"],
        "contradictions": ["Inventory could cushion the disruption."],
        "entity_resolution_results": {"NVDA": "company:NVDA"},
        "evidence_spans": ["A key supplier reported production delays."],
        "research_confidence": 0.6,
        "research_notes": "Near-term supply tightness could affect shipments.",
    }
    assert not any("HOLDS" in query or "SUPPLIES" in query for query, _ in run_calls)
    assert not any("HOLDS" in query or "SUPPLIES" in query for query, _ in statements)
