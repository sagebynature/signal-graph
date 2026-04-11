from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from signal_graph.cli.main import app
from tests.cli._journal_helpers import install_fake_journal_graph_client


def test_recall_signal_writes_markdown_artifact(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    install_fake_journal_graph_client(monkeypatch)

    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0
    first = runner.invoke(
        app,
        [
            "capture-signal",
            "--text",
            "Agent updated the deployment signal in the release notes.",
            "--origin-type",
            "agent_artifact",
            "--source-name",
            "codex",
            "--process",
            "codex",
            "--runtime-family",
            "codex",
            "--session-id",
            "session-1",
            "--what",
            "deployment",
            "--where",
            "notes/release.md",
        ],
    )
    second = runner.invoke(
        app,
        [
            "capture-signal",
            "--text",
            "External deployment signal confirms the rollout plan.",
            "--origin-type",
            "external_reference",
            "--source-name",
            "news",
            "--source-url",
            "https://example.com/rollout",
            "--what",
            "deployment",
            "--where",
            "https://example.com/rollout",
        ],
    )
    for raw in (first, second):
        signal_id = json.loads(raw.stdout)["signal_id"]
        assert runner.invoke(app, ["journalize-signal", "--signal", signal_id]).exit_code == 0

    result = runner.invoke(app, ["recall-signal", "--query", "deployment signal"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert len(payload["signal_ids"]) == 2
    assert "Signal Graph matched signals with provenance-rich recall." in payload["markdown_text"]
    assert payload["view"] == "ranked"
    assert payload["matches"][0]["explanation"]["score_components"]
    artifact_path = Path(payload["artifact_path"])
    assert artifact_path.is_file()


def test_recall_signal_supports_filter_only_lookup(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    install_fake_journal_graph_client(monkeypatch)

    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0
    capture = runner.invoke(
        app,
        [
            "capture-signal",
            "--text",
            "Agent deployment signal scoped to one session.",
            "--origin-type",
            "agent_artifact",
            "--source-name",
            "codex",
            "--runtime-family",
            "codex",
            "--session-id",
            "session-only",
            "--what",
            "deployment",
        ],
    )
    signal_id = json.loads(capture.stdout)["signal_id"]
    assert runner.invoke(app, ["journalize-signal", "--signal", signal_id]).exit_code == 0

    result = runner.invoke(
        app,
        [
            "recall-signal",
            "--session-id",
            "session-only",
            "--runtime-family",
            "codex",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["signal_ids"] == [signal_id]
    assert "filter-only recall" in payload["markdown_text"]


def test_recall_signal_supports_timeline_view_and_ordering(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    install_fake_journal_graph_client(monkeypatch)

    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0
    older = runner.invoke(
        app,
        [
            "capture-signal",
            "--text",
            "Deployment signal from earlier session.",
            "--origin-type",
            "user",
            "--source-name",
            "manual",
            "--observed-at",
            "2026-04-10T09:00:00+00:00",
            "--what",
            "deployment",
        ],
    )
    newer = runner.invoke(
        app,
        [
            "capture-signal",
            "--text",
            "Deployment signal from later session.",
            "--origin-type",
            "user",
            "--source-name",
            "manual",
            "--observed-at",
            "2026-04-11T09:00:00+00:00",
            "--what",
            "deployment",
        ],
    )
    for raw in (older, newer):
        signal_id = json.loads(raw.stdout)["signal_id"]
        assert runner.invoke(app, ["journalize-signal", "--signal", signal_id]).exit_code == 0

    result = runner.invoke(
        app,
        ["recall-signal", "--query", "deployment", "--view", "timeline"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["view"] == "timeline"
    assert payload["signal_ids"][0] == json.loads(newer.stdout)["signal_id"]


def test_recall_signal_rejects_unmatched_quote_query(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    install_fake_journal_graph_client(monkeypatch)

    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0

    result = runner.invoke(app, ["recall-signal", "--query", '"deployment'])

    assert result.exit_code == 1
    assert "unmatched double quote" in result.stdout
