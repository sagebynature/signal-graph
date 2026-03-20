from __future__ import annotations

import json

from neo4j.exceptions import ServiceUnavailable
from typer.testing import CliRunner

from signal_graph.cli.main import app
from signal_graph.config import DEFAULT_PROJECT_DIR
from signal_graph.models.research import ResearchBundleInput
from signal_graph.services.research import build_and_persist_research_bundle
from signal_graph.storage.sqlite import SqliteStore


def _candidate_row(
    ticker: str,
    matched_entity: str,
    relationship_path: list[str],
    path_length: int,
    *,
    asset_kind: str,
    event_type: str,
    direction: str,
) -> dict:
    return {
        "instrument_id": f"{asset_kind}:{ticker}",
        "ticker": ticker,
        "asset_kind": asset_kind,
        "matched_entity": matched_entity,
        "relationship_path": relationship_path,
        "path_length": path_length,
        "event_type": event_type,
        "direction": direction,
    }


def _install_fake_graph_client(monkeypatch) -> None:
    rows = [
        _candidate_row(
            "NVDA",
            "NVDA",
            ["DIRECT_ENTITY"],
            0,
            asset_kind="equity",
            event_type="supplier_disruption",
            direction="negative",
        ),
        _candidate_row(
            "SMH",
            "NVDA",
            ["HOLDS"],
            1,
            asset_kind="etf",
            event_type="supplier_disruption",
            direction="negative",
        ),
    ]

    monkeypatch.setenv("NEO4J_URI", "neo4j://127.0.0.1:1")

    class FakeGraphClient:
        def run(self, query: str, params: dict | None = None) -> list[dict]:
            return rows

        def run_in_transaction(
            self, statements: list[tuple[str, dict | None]]
        ) -> list[list[dict]]:
            return [[] for _ in statements]

        def close(self) -> None:
            return None

    monkeypatch.setattr("signal_graph.services.rank.GraphClient", FakeGraphClient)
    monkeypatch.setattr("signal_graph.cli.ingest.GraphClient", FakeGraphClient)


def _install_unresolved_company_graph_client(monkeypatch) -> None:
    rows = [
        {
            "ticker": "ACME",
            "matched_entity": "ACME",
            "relationship_path": ["DIRECT_ENTITY"],
            "path_length": 0,
            "event_type": "supplier_disruption",
            "direction": "negative",
        }
    ]

    monkeypatch.setenv("NEO4J_URI", "neo4j://127.0.0.1:1")

    class FakeGraphClient:
        def run(self, query: str, params: dict | None = None) -> list[dict]:
            return rows

        def run_in_transaction(
            self, statements: list[tuple[str, dict | None]]
        ) -> list[list[dict]]:
            return [[] for _ in statements]

        def close(self) -> None:
            return None

    monkeypatch.setattr("signal_graph.services.rank.GraphClient", FakeGraphClient)
    monkeypatch.setattr("signal_graph.cli.ingest.GraphClient", FakeGraphClient)


def _install_ordering_graph_client(monkeypatch) -> None:
    rows = [
        _candidate_row(
            "TSMC",
            "TSMC",
            ["DIRECT_ENTITY"],
            0,
            asset_kind="equity",
            event_type="supplier_disruption",
            direction="negative",
        ),
        _candidate_row(
            "NVDA",
            "TSMC",
            ["SUPPLIES_TO_CUSTOMER"],
            1,
            asset_kind="equity",
            event_type="supplier_disruption",
            direction="negative",
        ),
        _candidate_row(
            "SMH",
            "TSMC",
            ["HOLDS"],
            1,
            asset_kind="etf",
            event_type="supplier_disruption",
            direction="negative",
        ),
        _candidate_row(
            "SOXX",
            "TSMC",
            ["SUPPLIES_TO_CUSTOMER", "HOLDS"],
            2,
            asset_kind="etf",
            event_type="supplier_disruption",
            direction="negative",
        ),
    ]

    monkeypatch.setenv("NEO4J_URI", "neo4j://127.0.0.1:1")

    class FakeGraphClient:
        def run(self, query: str, params: dict | None = None) -> list[dict]:
            return rows

        def run_in_transaction(
            self, statements: list[tuple[str, dict | None]]
        ) -> list[list[dict]]:
            return [[] for _ in statements]

        def close(self) -> None:
            return None

    monkeypatch.setattr("signal_graph.services.rank.GraphClient", FakeGraphClient)
    monkeypatch.setattr("signal_graph.cli.ingest.GraphClient", FakeGraphClient)


def _install_event_type_graph_client(monkeypatch) -> None:
    rows = [
        _candidate_row(
            "TSMC",
            "TSMC",
            ["DIRECT_ENTITY"],
            0,
            asset_kind="equity",
            event_type="capex_cut",
            direction="negative",
        ),
        _candidate_row(
            "ASML",
            "TSMC",
            ["SUPPLIES_TO_AFFECTED"],
            1,
            asset_kind="equity",
            event_type="capex_cut",
            direction="negative",
        ),
        _candidate_row(
            "NVDA",
            "TSMC",
            ["SUPPLIES_TO_CUSTOMER"],
            1,
            asset_kind="equity",
            event_type="capex_cut",
            direction="negative",
        ),
        _candidate_row(
            "SMH",
            "TSMC",
            ["HOLDS"],
            1,
            asset_kind="etf",
            event_type="capex_cut",
            direction="negative",
        ),
    ]

    monkeypatch.setenv("NEO4J_URI", "neo4j://127.0.0.1:1")

    class FakeGraphClient:
        def run(self, query: str, params: dict | None = None) -> list[dict]:
            return rows

        def run_in_transaction(
            self, statements: list[tuple[str, dict | None]]
        ) -> list[list[dict]]:
            return [[] for _ in statements]

        def close(self) -> None:
            return None

    monkeypatch.setattr("signal_graph.services.rank.GraphClient", FakeGraphClient)
    monkeypatch.setattr("signal_graph.cli.ingest.GraphClient", FakeGraphClient)


def _install_configurable_graph_client(monkeypatch) -> None:
    rows = [
        _candidate_row(
            "NVDA",
            "NVDA",
            ["DIRECT_ENTITY"],
            0,
            asset_kind="equity",
            event_type="export_control",
            direction="negative",
        ),
        _candidate_row(
            "AMD",
            "NVDA",
            ["SUPPLIES_TO_CUSTOMER"],
            1,
            asset_kind="equity",
            event_type="export_control",
            direction="negative",
        ),
        _candidate_row(
            "SMH",
            "NVDA",
            ["HOLDS"],
            1,
            asset_kind="etf",
            event_type="export_control",
            direction="negative",
        ),
    ]

    monkeypatch.setenv("NEO4J_URI", "neo4j://127.0.0.1:1")

    class FakeGraphClient:
        def run(self, query: str, params: dict | None = None) -> list[dict]:
            return rows

        def run_in_transaction(
            self, statements: list[tuple[str, dict | None]]
        ) -> list[list[dict]]:
            return [[] for _ in statements]

        def close(self) -> None:
            return None

    monkeypatch.setattr("signal_graph.services.rank.GraphClient", FakeGraphClient)
    monkeypatch.setattr("signal_graph.cli.ingest.GraphClient", FakeGraphClient)


def _write_bundle_file(
    path,
    *,
    supporting_documents: list[str] | None = None,
    contradictions: list[str] | None = None,
    evidence_spans: list[str] | None = None,
    research_confidence: float = 0.6,
    research_notes: str = "Near-term supply tightness could affect shipments.",
) -> str:
    bundle_path = path / "bundle.json"
    bundle_path.write_text(
        json.dumps(
            {
                "supporting_documents": supporting_documents
                or ["https://example.com/nvda-supplier"],
                "contradictions": contradictions
                or ["Inventory could cushion the disruption."],
                "entity_resolution_results": {"NVDA": "company:NVDA"},
                "evidence_spans": evidence_spans
                or ["A key supplier reported production delays."],
                "research_confidence": research_confidence,
                "research_notes": research_notes,
            }
        )
    )
    return str(bundle_path)


def _write_scoring_policy_config(
    path,
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
        fallback_rationale = "For a negative `export_control`, local policy emphasizes instruments that move with immediate market access risk."

        [[scoring_policy.events.overrides]]
        relationship_path = ["HOLDS"]
        base_score = {base_score}
        timing_window = "immediate"
        rationale = "{rationale}"
        """
    )
    return str(config_path)


def test_rank_requires_initialized_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(app, ["rank", "--event", "ge-123"])

    assert result.exit_code == 1
    assert result.stdout.strip() == (
        "Project is not initialized. Run `signal-graph init` first."
    )


def test_rank_reports_graph_connectivity_failures_concisely(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def raise_connectivity_error(*_args, **_kwargs):
        raise ServiceUnavailable("neo4j is unavailable")

    monkeypatch.setattr("signal_graph.cli.rank.rank_event", raise_connectivity_error)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["rank", "--event", "ge-123"])

    assert result.exit_code == 1
    assert result.stdout.strip() == (
        "Unable to reach the graph database. Check Neo4j settings and try again."
    )


def test_rank_help_describes_graph_event_identifier():
    runner = CliRunner()

    result = runner.invoke(app, ["rank", "--help"])

    assert result.exit_code == 0
    assert "Graph event id to rank candidates for." in result.stdout


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
    candidates = json.loads(result.stdout)
    smh = next(candidate for candidate in candidates if candidate["ticker"] == "SMH")
    assert smh["instrument_id"] == "etf:SMH"
    assert smh["asset_kind"] == "etf"
    assert smh["matched_entity"] == "NVDA"
    assert smh["timing_window"] == "immediate"
    assert "HOLDS" in smh["relationship_path"]
    assert "NVDA" in smh["reason_summary"]
    assert smh["fast_reaction_score"] > 0.0
    assert smh["follow_through_score"] > 0.0


def test_rank_filters_unresolved_non_instrument_candidates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _install_unresolved_company_graph_client(monkeypatch)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "ACME supplier disruption"])
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
            "ACME",
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
    assert json.loads(result.stdout) == []


def test_rank_returns_instruments_only_for_trade_candidates(tmp_path, monkeypatch):
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
    candidates = json.loads(result.stdout)
    assert all(candidate["asset_kind"] in {"equity", "etf"} for candidate in candidates)
    assert all(
        candidate["instrument_id"] == f"{candidate['asset_kind']}:{candidate['ticker']}"
        for candidate in candidates
    )


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
    candidates = json.loads(result.stdout)
    assert [candidate["ticker"] for candidate in candidates] == [
        "TSMC",
        "NVDA",
        "SMH",
        "SOXX",
    ]
    nvda = next(candidate for candidate in candidates if candidate["ticker"] == "NVDA")
    assert nvda["asset_kind"] == "equity"
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
    candidates = json.loads(result.stdout)
    assert [candidate["ticker"] for candidate in candidates] == [
        "TSMC",
        "ASML",
        "SMH",
        "NVDA",
    ]
    asml = next(candidate for candidate in candidates if candidate["ticker"] == "ASML")
    nvda = next(candidate for candidate in candidates if candidate["ticker"] == "NVDA")
    assert asml["asset_kind"] == "equity"
    assert nvda["asset_kind"] == "equity"
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
    candidates = json.loads(result.stdout)
    assert [candidate["ticker"] for candidate in candidates] == [
        "NVDA",
        "SMH",
        "AMD",
    ]
    smh = next(candidate for candidate in candidates if candidate["ticker"] == "SMH")
    assert smh["asset_kind"] == "etf"
    assert (
        smh["reason_summary"] == "SMH is exposed to NVDA via policy-tuned ETF spillover"
    )


def test_rank_uses_ingested_research_bundle_revision_for_existing_graph_event(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    _install_configurable_graph_client(monkeypatch)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    _write_scoring_policy_config(
        tmp_path,
        description="revision-1 ETF spillover",
        rationale="Revision 1 rationale stays bound to the ingested graph event.",
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
            _write_bundle_file(
                tmp_path,
                supporting_documents=["https://example.com/export-control-r1"],
                contradictions=[],
                research_confidence=0.8,
                research_notes="Revision 1 research snapshot.",
            ),
        ],
    )

    store = SqliteStore(DEFAULT_PROJECT_DIR / "signal_graph.db")
    first_bundle = store.get_latest_research_bundle(event_candidate_id)
    assert first_bundle is not None
    assert first_bundle.bundle_revision == 1

    original_save_graph_event = SqliteStore.save_graph_event

    def save_graph_event_after_new_revision(self, graph_event):
        build_and_persist_research_bundle(
            self,
            graph_event.event_candidate_id,
            bundle_input=ResearchBundleInput(
                supporting_documents=["https://example.com/export-control-r2"],
                contradictions=["A new caveat was added after ingest."],
                evidence_spans=["Revision 2 evidence should not be rebound."],
                research_confidence=0.2,
                research_notes="Revision 2 research snapshot.",
            ),
        )
        return original_save_graph_event(self, graph_event)

    monkeypatch.setattr(
        "signal_graph.storage.sqlite.SqliteStore.save_graph_event",
        save_graph_event_after_new_revision,
    )

    ingested = runner.invoke(app, ["ingest", "--event-candidate", event_candidate_id])
    graph_event_id = json.loads(ingested.stdout)["graph_event_id"]

    graph_event = store.get_graph_event(graph_event_id)
    assert graph_event is not None
    assert graph_event.research_bundle_id == first_bundle.research_bundle_id

    latest_bundle = store.get_latest_research_bundle(event_candidate_id)
    assert latest_bundle is not None
    assert latest_bundle.research_bundle_id != first_bundle.research_bundle_id
    assert latest_bundle.bundle_revision == 2

    result = runner.invoke(app, ["rank", "--event", graph_event_id])

    assert result.exit_code == 0
    candidates = json.loads(result.stdout)
    smh = next(candidate for candidate in candidates if candidate["ticker"] == "SMH")
    assert smh["asset_kind"] == "etf"
    assert (
        smh["reason_summary"] == "SMH is exposed to NVDA via revision-1 ETF spillover"
    )
