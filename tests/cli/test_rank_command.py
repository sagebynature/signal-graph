from __future__ import annotations

import json

from typer.testing import CliRunner

from signal_graph.cli.main import app


def _install_fake_graph_client(monkeypatch) -> None:
    rows = [
        {
            "ticker": "NVDA",
            "matched_entity": "NVDA",
            "relationship_path": ["DIRECT_ENTITY"],
            "path_length": 0,
            "research_confidence": 0.6,
            "support_count": 1,
            "evidence_count": 1,
            "contradiction_count": 1,
        },
        {
            "ticker": "SMH",
            "matched_entity": "NVDA",
            "relationship_path": ["HOLDS"],
            "path_length": 1,
            "research_confidence": 0.6,
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


def _install_ordering_graph_client(monkeypatch) -> None:
    rows = [
        {
            "ticker": "TSMC",
            "matched_entity": "TSMC",
            "relationship_path": ["DIRECT_ENTITY"],
            "path_length": 0,
            "research_confidence": 0.8,
            "support_count": 2,
            "evidence_count": 2,
            "contradiction_count": 0,
            "event_type": "supplier_disruption",
            "direction": "negative",
        },
        {
            "ticker": "NVDA",
            "matched_entity": "TSMC",
            "relationship_path": ["SUPPLIES_TO_CUSTOMER"],
            "path_length": 1,
            "research_confidence": 0.8,
            "support_count": 2,
            "evidence_count": 2,
            "contradiction_count": 0,
            "event_type": "supplier_disruption",
            "direction": "negative",
        },
        {
            "ticker": "SMH",
            "matched_entity": "TSMC",
            "relationship_path": ["HOLDS"],
            "path_length": 1,
            "research_confidence": 0.8,
            "support_count": 2,
            "evidence_count": 2,
            "contradiction_count": 0,
            "event_type": "supplier_disruption",
            "direction": "negative",
        },
        {
            "ticker": "SOXX",
            "matched_entity": "TSMC",
            "relationship_path": ["SUPPLIES_TO_CUSTOMER", "HOLDS"],
            "path_length": 2,
            "research_confidence": 0.8,
            "support_count": 2,
            "evidence_count": 2,
            "contradiction_count": 0,
            "event_type": "supplier_disruption",
            "direction": "negative",
        },
    ]

    class FakeGraphClient:
        def run(self, query: str, params: dict | None = None) -> list[dict]:
            return rows

        def close(self) -> None:
            return None

    monkeypatch.setattr("signal_graph.services.rank.GraphClient", FakeGraphClient)


def _install_event_type_graph_client(monkeypatch) -> None:
    rows = [
        {
            "ticker": "TSMC",
            "matched_entity": "TSMC",
            "relationship_path": ["DIRECT_ENTITY"],
            "path_length": 0,
            "research_confidence": 0.8,
            "support_count": 2,
            "evidence_count": 2,
            "contradiction_count": 0,
            "event_type": "capex_cut",
            "direction": "negative",
        },
        {
            "ticker": "ASML",
            "matched_entity": "TSMC",
            "relationship_path": ["SUPPLIES_TO_AFFECTED"],
            "path_length": 1,
            "research_confidence": 0.8,
            "support_count": 2,
            "evidence_count": 2,
            "contradiction_count": 0,
            "event_type": "capex_cut",
            "direction": "negative",
        },
        {
            "ticker": "NVDA",
            "matched_entity": "TSMC",
            "relationship_path": ["SUPPLIES_TO_CUSTOMER"],
            "path_length": 1,
            "research_confidence": 0.8,
            "support_count": 2,
            "evidence_count": 2,
            "contradiction_count": 0,
            "event_type": "capex_cut",
            "direction": "negative",
        },
        {
            "ticker": "SMH",
            "matched_entity": "TSMC",
            "relationship_path": ["HOLDS"],
            "path_length": 1,
            "research_confidence": 0.8,
            "support_count": 2,
            "evidence_count": 2,
            "contradiction_count": 0,
            "event_type": "capex_cut",
            "direction": "negative",
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
            "research_confidence": 0.8,
            "support_count": 2,
            "evidence_count": 2,
            "contradiction_count": 0,
            "event_type": "export_control",
            "direction": "negative",
        },
        {
            "ticker": "AMD",
            "matched_entity": "NVDA",
            "relationship_path": ["SUPPLIES_TO_CUSTOMER"],
            "path_length": 1,
            "research_confidence": 0.8,
            "support_count": 2,
            "evidence_count": 2,
            "contradiction_count": 0,
            "event_type": "export_control",
            "direction": "negative",
        },
        {
            "ticker": "SMH",
            "matched_entity": "NVDA",
            "relationship_path": ["HOLDS"],
            "path_length": 1,
            "research_confidence": 0.8,
            "support_count": 2,
            "evidence_count": 2,
            "contradiction_count": 0,
            "event_type": "export_control",
            "direction": "negative",
        },
    ]

    class FakeGraphClient:
        def run(self, query: str, params: dict | None = None) -> list[dict]:
            return rows

        def close(self) -> None:
            return None

    monkeypatch.setattr("signal_graph.services.rank.GraphClient", FakeGraphClient)


def _write_bundle_file(path) -> str:
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
    return str(bundle_path)


def _write_scoring_policy_config(path) -> str:
    config_path = path / ".signal-graph" / "config.toml"
    config_path.write_text(
        """
        [scoring_policy]

        [[scoring_policy.paths]]
        relationship_path = ["HOLDS"]
        description = "policy-tuned ETF spillover"
        base_score = 0.5
        timing_window = "immediate"

        [[scoring_policy.events]]
        event_type = "export_control"
        direction = "negative"
        fallback_rationale = "For a negative `export_control`, local policy emphasizes instruments that move with immediate market access risk."

        [[scoring_policy.events.overrides]]
        relationship_path = ["HOLDS"]
        base_score = 0.64
        timing_window = "immediate"
        rationale = "For a negative `export_control`, sector ETF exposure can move immediately."
        """
    )
    return str(config_path)


def test_rank_returns_graph_backed_candidates_with_reasons(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _install_fake_graph_client(monkeypatch)

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

    result = runner.invoke(app, ["rank", "--event", graph_event_id])

    assert result.exit_code == 0
    candidates = json.loads(result.stdout.replace("'", '"'))
    smh = next(candidate for candidate in candidates if candidate["ticker"] == "SMH")
    assert smh["matched_entity"] == "NVDA"
    assert smh["timing_window"] == "immediate"
    assert "HOLDS" in smh["relationship_path"]
    assert "NVDA" in smh["reason_summary"]
    assert smh["fast_reaction_score"] > 0.0
    assert smh["follow_through_score"] > 0.0


def test_rank_prefers_supplier_spillover_over_broad_etf_holding(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _install_ordering_graph_client(monkeypatch)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "TSMC supplier disruption"])
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

    result = runner.invoke(app, ["rank", "--event", graph_event_id])

    assert result.exit_code == 0
    candidates = json.loads(result.stdout.replace("'", '"'))
    assert [candidate["ticker"] for candidate in candidates] == [
        "TSMC",
        "NVDA",
        "SMH",
        "SOXX",
    ]
    nvda = next(candidate for candidate in candidates if candidate["ticker"] == "NVDA")
    assert nvda["timing_window"] == "immediate"


def test_rank_treats_capex_cut_as_more_relevant_for_upstream_suppliers(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    _install_event_type_graph_client(monkeypatch)

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

    result = runner.invoke(app, ["rank", "--event", graph_event_id])

    assert result.exit_code == 0
    candidates = json.loads(result.stdout.replace("'", '"'))
    assert [candidate["ticker"] for candidate in candidates] == [
        "TSMC",
        "ASML",
        "SMH",
        "NVDA",
    ]
    asml = next(candidate for candidate in candidates if candidate["ticker"] == "ASML")
    nvda = next(candidate for candidate in candidates if candidate["ticker"] == "NVDA")
    assert asml["timing_window"] == "immediate"
    assert nvda["timing_window"] == "short_drift"


def test_rank_uses_local_export_control_policy(tmp_path, monkeypatch):
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

    result = runner.invoke(app, ["rank", "--event", graph_event_id])

    assert result.exit_code == 0
    candidates = json.loads(result.stdout.replace("'", '"'))
    assert [candidate["ticker"] for candidate in candidates] == [
        "NVDA",
        "SMH",
        "AMD",
    ]
    smh = next(candidate for candidate in candidates if candidate["ticker"] == "SMH")
    assert (
        smh["reason_summary"] == "SMH is exposed to NVDA via policy-tuned ETF spillover"
    )
