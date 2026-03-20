from __future__ import annotations

import json
from pathlib import Path

from neo4j.exceptions import ServiceUnavailable
from typer.testing import CliRunner

from signal_graph.cli.main import app


def _install_fake_graph_client(monkeypatch) -> None:
    rows = [
        {
            "ticker": "TSMC",
            "matched_entity": "TSMC",
            "relationship_path": ["DIRECT_ENTITY"],
            "path_length": 0,
            "event_type": "capex_cut",
            "direction": "negative",
            "research_confidence": 0.7,
            "support_count": 1,
            "evidence_count": 1,
            "contradiction_count": 1,
        },
        {
            "ticker": "SMH",
            "matched_entity": "TSMC",
            "relationship_path": ["HOLDS"],
            "path_length": 1,
            "event_type": "capex_cut",
            "direction": "negative",
            "research_confidence": 0.7,
            "support_count": 1,
            "evidence_count": 1,
            "contradiction_count": 1,
        },
    ]

    class FakeGraphClient:
        def run(self, query: str, params: dict | None = None) -> list[dict]:
            return rows

        def close(self) -> None:
            return None

    monkeypatch.setattr("signal_graph.services.rank.GraphClient", FakeGraphClient)


def _install_configurable_graph_client(monkeypatch) -> None:
    rows = [
        {
            "ticker": "NVDA",
            "matched_entity": "NVDA",
            "relationship_path": ["DIRECT_ENTITY"],
            "path_length": 0,
            "event_type": "export_control",
            "direction": "negative",
            "research_confidence": 0.7,
            "support_count": 1,
            "evidence_count": 1,
            "contradiction_count": 1,
        },
        {
            "ticker": "SMH",
            "matched_entity": "NVDA",
            "relationship_path": ["HOLDS"],
            "path_length": 1,
            "event_type": "export_control",
            "direction": "negative",
            "research_confidence": 0.7,
            "support_count": 1,
            "evidence_count": 1,
            "contradiction_count": 1,
        },
    ]

    class FakeGraphClient:
        def run(self, query: str, params: dict | None = None) -> list[dict]:
            return rows

        def close(self) -> None:
            return None

    monkeypatch.setattr("signal_graph.services.rank.GraphClient", FakeGraphClient)


def _write_bundle_file(path: Path) -> str:
    bundle_path = path / "bundle.json"
    bundle_path.write_text(
        json.dumps(
            {
                "supporting_documents": ["https://example.com/tsmc-capex"],
                "contradictions": ["Demand recovery may blunt the impact."],
                "entity_resolution_results": {"TSMC": "company:TSMC"},
                "evidence_spans": ["TSMC said it would reduce capital spending."],
                "research_confidence": 0.7,
                "research_notes": "Capex cuts may pressure semiconductor equipment demand.",
            }
        )
    )
    return str(bundle_path)


def _write_scoring_policy_config(
    path: Path,
    *,
    description: str = "policy-tuned ETF spillover",
    rationale: str = (
        "For a negative `export_control`, sector ETF exposure can move immediately."
    ),
    base_score: float = 0.64,
) -> str:
    config_path = path / ".signal-graph" / "config.toml"
    config_path.write_text(
        f"""
        [scoring_policy]

        [[scoring_policy.paths]]
        relationship_path = ["HOLDS"]
        description = "{description}"
        base_score = 0.5
        timing_window = "immediate"

        [[scoring_policy.events]]
        event_type = "export_control"
        direction = "negative"

        [[scoring_policy.events.overrides]]
        relationship_path = ["HOLDS"]
        base_score = {base_score}
        timing_window = "immediate"
        rationale = "{rationale}"
        """
    )
    return str(config_path)


def test_explain_requires_initialized_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(app, ["explain", "--event", "ge-123", "--candidate", "NVDA"])

    assert result.exit_code == 1
    assert result.stdout.strip() == (
        "Project is not initialized. Run `signal-graph init` first."
    )


def test_explain_reports_graph_connectivity_failures_concisely(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def raise_connectivity_error(*_args, **_kwargs):
        raise ServiceUnavailable("neo4j is unavailable")

    monkeypatch.setattr(
        "signal_graph.cli.explain.write_memo_artifact", raise_connectivity_error
    )

    runner = CliRunner()
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["explain", "--event", "ge-123", "--candidate", "NVDA"])

    assert result.exit_code == 1
    assert result.stdout.strip() == (
        "Unable to reach the graph database. Check Neo4j settings and try again."
    )


def test_explain_help_describes_identifiers():
    runner = CliRunner()

    result = runner.invoke(app, ["explain", "--help"])

    assert result.exit_code == 0
    assert "Graph event id to explain." in result.stdout
    assert "Candidate ticker symbol to explain." in result.stdout


def test_explain_outputs_provenance_backed_sections(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _install_fake_graph_client(monkeypatch)

    runner = CliRunner()
    runner.invoke(app, ["init"])
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
    runner.invoke(
        app,
        [
            "research",
            "--event-candidate",
            event_candidate_id,
            "--bundle-file",
            _write_bundle_file(tmp_path),
        ],
    )
    ingested = runner.invoke(app, ["ingest", "--event-candidate", event_candidate_id])
    graph_event_id = json.loads(ingested.stdout)["graph_event_id"]

    result = runner.invoke(
        app, ["explain", "--event", graph_event_id, "--candidate", "SMH"]
    )

    assert result.exit_code == 0
    assert "Confirmed fact: Event `TSMC cuts capex`" in result.stdout
    assert "https://example.com/tsmc-capex" in result.stdout
    assert "Graph implication: Candidate `SMH` is linked to `TSMC`" in result.stdout
    assert "via ETF holding exposure" in result.stdout
    assert "For a negative `capex_cut`" in result.stdout
    assert "Assistant inference: `SMH` scores" in result.stdout
    assert "Demand recovery may blunt the impact." in result.stdout
    assert "HOLDS" not in result.stdout


def test_explain_writes_evidence_backed_markdown_artifact(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _install_fake_graph_client(monkeypatch)

    runner = CliRunner()
    runner.invoke(app, ["init"])
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
    runner.invoke(
        app,
        [
            "research",
            "--event-candidate",
            event_candidate_id,
            "--bundle-file",
            _write_bundle_file(tmp_path),
        ],
    )
    ingested = runner.invoke(app, ["ingest", "--event-candidate", event_candidate_id])
    graph_event_id = json.loads(ingested.stdout)["graph_event_id"]

    result = runner.invoke(
        app, ["explain", "--event", graph_event_id, "--candidate", "SMH"]
    )

    assert result.exit_code == 0
    artifact_path = Path(f".signal-graph/artifacts/{graph_event_id}-SMH.md")
    assert artifact_path.is_file()
    artifact_text = artifact_path.read_text()
    assert "Confirmed fact: Event `TSMC cuts capex`" in artifact_text
    assert "Graph implication: Candidate `SMH` is linked to `TSMC`" in artifact_text
    assert "via ETF holding exposure" in artifact_text
    assert "For a negative `capex_cut`" in artifact_text
    assert "Assistant inference: `SMH` scores" in artifact_text
    assert "HOLDS" not in artifact_text


def test_explain_uses_local_policy_rationale(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _install_configurable_graph_client(monkeypatch)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    _write_scoring_policy_config(tmp_path)
    submit = runner.invoke(app, ["submit", "--text", "US export controls tighten"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]
    normalized = runner.invoke(
        app,
        [
            "normalize",
            "--raw-item",
            raw_item_id,
            "--event-type",
            "export_control",
            "--direction",
            "negative",
            "--primary-entity",
            "NVDA",
        ],
    )
    event_candidate_id = json.loads(normalized.stdout)["event_candidate_id"]
    runner.invoke(
        app,
        [
            "research",
            "--event-candidate",
            event_candidate_id,
            "--bundle-file",
            _write_bundle_file(tmp_path),
        ],
    )
    ingested = runner.invoke(app, ["ingest", "--event-candidate", event_candidate_id])
    graph_event_id = json.loads(ingested.stdout)["graph_event_id"]

    result = runner.invoke(
        app, ["explain", "--event", graph_event_id, "--candidate", "SMH"]
    )

    assert result.exit_code == 0
    assert "policy-tuned ETF spillover" in result.stdout
    assert "For a negative `export_control`" in result.stdout


def test_explain_keeps_existing_memo_stable_after_policy_change(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _install_configurable_graph_client(monkeypatch)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    _write_scoring_policy_config(
        tmp_path,
        description="snapshot ETF spillover",
        rationale="Snapshot rationale should stay stable for the ingested graph event.",
    )
    submit = runner.invoke(app, ["submit", "--text", "US export controls tighten"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]
    normalized = runner.invoke(
        app,
        [
            "normalize",
            "--raw-item",
            raw_item_id,
            "--event-type",
            "export_control",
            "--direction",
            "negative",
            "--primary-entity",
            "NVDA",
        ],
    )
    event_candidate_id = json.loads(normalized.stdout)["event_candidate_id"]
    runner.invoke(
        app,
        [
            "research",
            "--event-candidate",
            event_candidate_id,
            "--bundle-file",
            _write_bundle_file(tmp_path),
        ],
    )
    ingested = runner.invoke(app, ["ingest", "--event-candidate", event_candidate_id])
    graph_event_id = json.loads(ingested.stdout)["graph_event_id"]

    original = runner.invoke(
        app, ["explain", "--event", graph_event_id, "--candidate", "SMH"]
    )

    assert original.exit_code == 0
    assert "snapshot ETF spillover" in original.stdout
    assert "Snapshot rationale should stay stable" in original.stdout

    _write_scoring_policy_config(
        tmp_path,
        description="mutated ETF spillover",
        rationale="Mutated rationale should not appear for the existing graph event.",
        base_score=0.12,
    )
    replayed = runner.invoke(
        app, ["explain", "--event", graph_event_id, "--candidate", "SMH"]
    )

    assert replayed.exit_code == 0
    assert replayed.stdout == original.stdout
    assert "snapshot ETF spillover" in replayed.stdout
    assert "Snapshot rationale should stay stable" in replayed.stdout
    assert "mutated ETF spillover" not in replayed.stdout
    assert "Mutated rationale should not appear" not in replayed.stdout
