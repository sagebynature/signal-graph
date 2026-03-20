from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from signal_graph.cli.main import app


def test_manual_event_flow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0
    submit = runner.invoke(app, ["submit", "--text", "TSMC cuts capex"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]
    normalized = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])
    event_candidate_id = json.loads(normalized.stdout)["event_candidate_id"]
    assert runner.invoke(app, ["research", "--event-candidate", event_candidate_id]).exit_code == 0
    ingested = runner.invoke(app, ["ingest", "--event-candidate", event_candidate_id])
    graph_event_id = json.loads(ingested.stdout)["graph_event_id"]
    assert runner.invoke(app, ["rank", "--event", graph_event_id]).exit_code == 0
    assert (
        runner.invoke(app, ["explain", "--event", graph_event_id, "--candidate", "SMH"]).exit_code
        == 0
    )
    assert Path(".signal-graph/artifacts").is_dir()
