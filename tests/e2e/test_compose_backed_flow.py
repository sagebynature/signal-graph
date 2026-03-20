from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from signal_graph.cli.main import app
from signal_graph.graph.client import GraphClient
from signal_graph.graph.schema import demo_reference_graph_statements

_INTEGRATION_ENV_VAR = "SIGNAL_GRAPH_RUN_INTEGRATION"


def _integration_enabled() -> bool:
    return (
        os.getenv(_INTEGRATION_ENV_VAR) == "1" or os.getenv("CI", "").lower() == "true"
    )


_SKIP_IF_NO_INTEGRATION_ENV = pytest.mark.skipif(
    not _integration_enabled(),
    reason="integration test requires live Neo4j; set SIGNAL_GRAPH_RUN_INTEGRATION=1 or run in CI",
)


def _seed_demo_reference_graph() -> None:
    client = GraphClient()
    try:
        client.run_in_transaction(demo_reference_graph_statements())
    finally:
        client.close()


@pytest.mark.integration
@_SKIP_IF_NO_INTEGRATION_ENV
def test_compose_backed_flow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0
    _seed_demo_reference_graph()

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
    assert ingested.exit_code == 0
    graph_event_id = json.loads(ingested.stdout)["graph_event_id"]

    ranked = runner.invoke(app, ["rank", "--event", graph_event_id])
    assert ranked.exit_code == 0
    ranked_candidates = json.loads(ranked.stdout)
    assert any(candidate["ticker"] == "SMH" for candidate in ranked_candidates)
    assert all(
        candidate["asset_kind"] in {"equity", "etf"} for candidate in ranked_candidates
    )

    explained = runner.invoke(
        app, ["explain", "--event", graph_event_id, "--candidate", "SMH"]
    )
    assert explained.exit_code == 0
    assert "Confirmed fact: Event `TSMC cuts capex`" in explained.stdout
    assert Path(".signal-graph/artifacts").is_dir()
