from __future__ import annotations

from signal_graph.services.scoring_policy import get_scoring_policy


def test_policy_resolves_capex_cut_upstream_supplier_override():
    resolved = get_scoring_policy().resolve(
        ["SUPPLIES_TO_AFFECTED"], event_type="capex_cut", direction="negative"
    )

    assert resolved.base_score == 0.62
    assert resolved.timing_window == "immediate"
    assert resolved.description == "upstream supplier exposure"
    assert resolved.rationale is not None
    assert "upstream suppliers can react quickly" in resolved.rationale


def test_policy_resolves_supplier_disruption_customer_spillover():
    resolved = get_scoring_policy().resolve(
        ["SUPPLIES_TO_CUSTOMER"],
        event_type="supplier_disruption",
        direction="negative",
    )

    assert resolved.base_score == 0.58
    assert resolved.timing_window == "immediate"
    assert resolved.description == "downstream customer spillover"
    assert resolved.rationale is not None
    assert "downstream customers often react quickly" in resolved.rationale
