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
                "supporting_documents": ["https://example.com/tsmc-capex"],
                "contradictions": ["Demand recovery may offset the capex cut."],
                "entity_resolution_results": {"TSMC": "company:TSMC"},
                "evidence_spans": ["TSMC said it would reduce capital spending."],
                "research_confidence": 0.7,
                "research_notes": "Capex cuts often pressure semiconductor equipment demand.",
            }
        )
    )
    return bundle_path


def test_research_requires_initialized_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(app, ["research", "--event-candidate", "ec-123"])

    assert result.exit_code == 1
    assert result.stdout.strip() == (
        "Project is not initialized. Run `signal-graph init` first."
    )


def test_research_help_describes_event_candidate_identifier():
    runner = CliRunner()

    result = runner.invoke(app, ["research", "--help"])

    assert result.exit_code == 0
    assert "Event candidate id to attach research to." in result.stdout


def test_research_creates_bundle_from_bundle_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]
    normalized = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])
    event_candidate_id = json.loads(normalized.stdout)["event_candidate_id"]
    bundle_path = _write_bundle_file(tmp_path)

    result = runner.invoke(
        app,
        [
            "research",
            "--event-candidate",
            event_candidate_id,
            "--bundle-file",
            str(bundle_path),
        ],
    )

    assert result.exit_code == 0
    research_bundle = json.loads(result.stdout)
    assert research_bundle["research_bundle_id"] == f"rb-{event_candidate_id}"
    assert research_bundle["supporting_documents"] == ["https://example.com/tsmc-capex"]


def test_research_persists_bundle_fields_for_event_candidate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]
    normalized = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])
    event_candidate_id = json.loads(normalized.stdout)["event_candidate_id"]
    bundle_path = _write_bundle_file(tmp_path)

    result = runner.invoke(
        app,
        [
            "research",
            "--event-candidate",
            event_candidate_id,
            "--bundle-file",
            str(bundle_path),
        ],
    )

    assert result.exit_code == 0
    research_bundle = json.loads(result.stdout)
    database_path = Path(".signal-graph/signal_graph.db")

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT
                research_bundle_id,
                event_candidate_id,
                supporting_documents,
                contradictions,
                entity_resolution_results,
                evidence_spans,
                research_confidence,
                research_notes
            FROM research_bundles
            WHERE research_bundle_id = ?
            """,
            (research_bundle["research_bundle_id"],),
        ).fetchone()

    assert row == (
        research_bundle["research_bundle_id"],
        event_candidate_id,
        json.dumps(["https://example.com/tsmc-capex"]),
        json.dumps(["Demand recovery may offset the capex cut."]),
        json.dumps({"TSMC": "company:TSMC"}),
        json.dumps(["TSMC said it would reduce capital spending."]),
        0.7,
        "Capex cuts often pressure semiconductor equipment demand.",
    )


def test_research_preserves_multiple_revisions_for_same_event_candidate(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]
    normalized = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])
    event_candidate_id = json.loads(normalized.stdout)["event_candidate_id"]
    first_bundle_path = _write_bundle_file(tmp_path)
    second_bundle_path = tmp_path / "bundle-revision-2.json"
    second_bundle_path.write_text(
        json.dumps(
            {
                "supporting_documents": ["https://example.com/tsmc-capex-revision-2"],
                "contradictions": ["Supplier commentary softened the demand outlook."],
                "entity_resolution_results": {"TSMC": "company:TSMC"},
                "evidence_spans": ["Management revised the supplier forecast."],
                "research_confidence": 0.8,
                "research_notes": "Revision two keeps the earlier evidence but updates the conclusion.",
            }
        )
    )

    first_result = runner.invoke(
        app,
        [
            "research",
            "--event-candidate",
            event_candidate_id,
            "--bundle-file",
            str(first_bundle_path),
        ],
    )
    second_result = runner.invoke(
        app,
        [
            "research",
            "--event-candidate",
            event_candidate_id,
            "--bundle-file",
            str(second_bundle_path),
        ],
    )

    assert first_result.exit_code == 0
    assert second_result.exit_code == 0

    first_bundle = json.loads(first_result.stdout)
    second_bundle = json.loads(second_result.stdout)
    assert first_bundle["research_bundle_id"] == f"rb-{event_candidate_id}"
    assert first_bundle["research_bundle_id"] != second_bundle["research_bundle_id"]
    assert second_bundle["research_bundle_id"] == f"rb-{event_candidate_id}-r0002"

    with sqlite3.connect(Path(".signal-graph/signal_graph.db")) as connection:
        rows = connection.execute(
            """
            SELECT research_bundle_id, research_notes
            FROM research_bundles
            WHERE event_candidate_id = ?
            ORDER BY bundle_revision
            """,
            (event_candidate_id,),
        ).fetchall()

    assert rows == [
        (
            first_bundle["research_bundle_id"],
            "Capex cuts often pressure semiconductor equipment demand.",
        ),
        (
            second_bundle["research_bundle_id"],
            "Revision two keeps the earlier evidence but updates the conclusion.",
        ),
    ]


def test_research_rejects_empty_bundle_without_allow_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]
    normalized = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])
    event_candidate_id = json.loads(normalized.stdout)["event_candidate_id"]
    empty_bundle_path = tmp_path / "empty-bundle.json"
    empty_bundle_path.write_text("{}")

    result = runner.invoke(
        app,
        [
            "research",
            "--event-candidate",
            event_candidate_id,
            "--bundle-file",
            str(empty_bundle_path),
        ],
    )

    assert result.exit_code != 0
    assert "empty research bundle" in result.stdout.lower()


def test_research_allows_empty_bundle_when_explicitly_requested(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]
    normalized = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])
    event_candidate_id = json.loads(normalized.stdout)["event_candidate_id"]

    result = runner.invoke(
        app,
        ["research", "--event-candidate", event_candidate_id, "--allow-empty"],
    )

    assert result.exit_code == 0
    research_bundle = json.loads(result.stdout)
    assert research_bundle["research_bundle_id"] == f"rb-{event_candidate_id}"
    assert research_bundle["supporting_documents"] == []
    assert research_bundle["contradictions"] == []

    with sqlite3.connect(Path(".signal-graph/signal_graph.db")) as connection:
        row = connection.execute(
            """
            SELECT research_bundle_id, event_candidate_id
            FROM research_bundles
            WHERE research_bundle_id = ?
            """,
            (research_bundle["research_bundle_id"],),
        ).fetchone()

    assert row == (
        research_bundle["research_bundle_id"],
        event_candidate_id,
    )
