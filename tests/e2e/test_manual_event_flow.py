from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from signal_graph.cli.main import app
from signal_graph.graph.client import GraphClient
from signal_graph.graph.schema import demo_reference_graph_statements


def _seed_demo_reference_graph() -> None:
    client = GraphClient()
    try:
        client.run_in_transaction(demo_reference_graph_statements())
    finally:
        client.close()


def test_manual_event_flow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0
    _seed_demo_reference_graph()
    submit = runner.invoke(app, ["submit", "--text", "TSMC cuts capex"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]
    normalized = runner.invoke(
        app,
        [
            "normalize",
            "--raw-item",
            raw_item_id,
            "--event-type",
            "capex_cut",
            "--direction",
            "negative",
            "--primary-entity",
            "TSMC",
        ],
    )
    event_candidate_id = json.loads(normalized.stdout)["event_candidate_id"]
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(
        json.dumps(
            {
                "supporting_documents": ["https://example.com/tsmc-capex"],
                "evidence_spans": ["TSMC said it would reduce capital spending."],
                "research_confidence": 0.7,
            }
        )
    )
    assert (
        runner.invoke(
            app,
            [
                "research",
                "--event-candidate",
                event_candidate_id,
                "--bundle-file",
                str(bundle_path),
            ],
        ).exit_code
        == 0
    )
    ingested = runner.invoke(app, ["ingest", "--event-candidate", event_candidate_id])
    graph_event_id = json.loads(ingested.stdout)["graph_event_id"]
    assert runner.invoke(app, ["rank", "--event", graph_event_id]).exit_code == 0
    assert (
        runner.invoke(
            app, ["explain", "--event", graph_event_id, "--candidate", "SMH"]
        ).exit_code
        == 0
    )
    assert Path(".signal-graph/artifacts").is_dir()
