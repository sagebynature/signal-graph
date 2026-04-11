from __future__ import annotations

import json

from typer.testing import CliRunner

from signal_graph.cli.main import app
from signal_graph.models.journal import MINIMUM_PROVENANCE_FIELDS
from tests.cli._journal_helpers import install_fake_journal_graph_client


def test_signal_journal_flow_proves_multi_session_determinism(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    install_fake_journal_graph_client(monkeypatch)

    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0

    capture_specs = [
        ("user", "manual", "session-u1", "User signal about deployment readiness."),
        ("agent_artifact", "codex", "session-a1", "Agent signal about deployment checklist completion."),
        ("external_reference", "news", "session-r1", "External reference signal about deployment policy."),
        ("agent_artifact", "codex", "session-a2", "Agent signal about deployment rollback rehearsal."),
        ("user", "manual", "session-u2", "User signal about deployment sign-off."),
    ]
    signal_ids: list[str] = []

    for origin_type, source_name, session_id, text in capture_specs:
        result = runner.invoke(
            app,
            [
                "capture-signal",
                "--text",
                text,
                "--origin-type",
                origin_type,
                "--source-name",
                source_name,
                "--session-id",
                session_id,
                "--runtime-family",
                "codex" if origin_type == "agent_artifact" else "human",
                "--what",
                "deployment",
                "--where",
                f"workspace/{session_id}.md",
                "--intent-status",
                "explicit" if origin_type != "external_reference" else "unknown",
                *(
                    ["--why", "Support a safe deployment decision."]
                    if origin_type != "external_reference"
                    else []
                ),
            ],
        )
        assert result.exit_code == 0
        signal_id = json.loads(result.stdout)["signal_id"]
        signal_ids.append(signal_id)
        assert runner.invoke(app, ["journalize-signal", "--signal", signal_id]).exit_code == 0

    first_recall = runner.invoke(app, ["recall-signal", "--query", "deployment signal", "--limit", "5"])
    second_recall = runner.invoke(app, ["recall-signal", "--query", "deployment signal", "--limit", "5"])

    assert first_recall.exit_code == 0
    assert second_recall.exit_code == 0
    first_payload = json.loads(first_recall.stdout)
    second_payload = json.loads(second_recall.stdout)

    assert set(first_payload["signal_ids"]) == set(signal_ids)
    assert first_payload["signal_ids"] == second_payload["signal_ids"]
    assert first_payload["markdown_text"] == second_payload["markdown_text"]
    assert first_payload["graph_paths"] == second_payload["graph_paths"]
    assert first_payload["provenance_contract"]["required_fields"] == MINIMUM_PROVENANCE_FIELDS
