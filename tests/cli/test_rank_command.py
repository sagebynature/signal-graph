from __future__ import annotations

import json

from typer.testing import CliRunner

from trade_graph.cli.main import app


def test_rank_returns_candidates_with_scores(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]
    normalized = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])
    event_candidate_id = json.loads(normalized.stdout)["event_candidate_id"]
    runner.invoke(app, ["research", "--event-candidate", event_candidate_id])
    ingested = runner.invoke(app, ["ingest", "--event-candidate", event_candidate_id])
    graph_event_id = json.loads(ingested.stdout)["graph_event_id"]

    result = runner.invoke(app, ["rank", "--event", graph_event_id])

    assert result.exit_code == 0
    assert "fast_reaction_score" in result.stdout
