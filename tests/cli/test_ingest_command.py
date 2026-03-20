from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from typer.testing import CliRunner

from signal_graph.cli.main import app


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
    monkeypatch, calls: list[tuple[str, dict | None]]
) -> None:
    class FakeGraphClient:
        def run(self, query: str, params: dict | None = None) -> list[dict]:
            calls.append((query, params))
            return []

        def close(self) -> None:
            return None

    monkeypatch.setattr("signal_graph.cli.ingest.GraphClient", FakeGraphClient)


def test_ingest_creates_graph_event_record(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls: list[tuple[str, dict | None]] = []
    _install_fake_graph_client(monkeypatch, calls)

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


def test_ingest_persists_graph_event_record(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls: list[tuple[str, dict | None]] = []
    _install_fake_graph_client(monkeypatch, calls)

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


def test_ingest_sends_rich_graph_payload_and_seed_queries(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    calls: list[tuple[str, dict | None]] = []
    _install_fake_graph_client(monkeypatch, calls)

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
    assert len(calls) >= 3

    graph_query, graph_params = calls[-1]
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
    assert any("ticker: 'NVDA'" in query for query, _ in calls[:-1])
