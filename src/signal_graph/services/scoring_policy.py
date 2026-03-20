from __future__ import annotations

from signal_graph.models.policy import (
    EventPolicy,
    EventPolicyOverride,
    PathPolicy,
    ScoringPolicy,
)

_DEFAULT_SCORING_POLICY = ScoringPolicy(
    path_policies=[
        PathPolicy(
            relationship_path=("DIRECT_ENTITY",),
            description="direct company exposure",
            base_score=0.7,
            timing_window="immediate",
        ),
        PathPolicy(
            relationship_path=("HOLDS",),
            description="ETF holding exposure",
            base_score=0.5,
            timing_window="immediate",
        ),
        PathPolicy(
            relationship_path=("SUPPLIES_TO_CUSTOMER",),
            description="downstream customer spillover",
            base_score=0.58,
            timing_window="short_drift",
        ),
        PathPolicy(
            relationship_path=("SUPPLIES_TO_AFFECTED",),
            description="upstream supplier exposure",
            base_score=0.44,
            timing_window="short_drift",
        ),
        PathPolicy(
            relationship_path=("SUPPLIES_TO_CUSTOMER", "HOLDS"),
            description="ETF exposure to downstream customer spillover",
            base_score=0.38,
            timing_window="immediate",
        ),
        PathPolicy(
            relationship_path=("SUPPLIES_TO_AFFECTED", "HOLDS"),
            description="ETF exposure to upstream supplier pressure",
            base_score=0.32,
            timing_window="immediate",
        ),
    ],
    event_policies=[
        EventPolicy(
            event_type="capex_cut",
            direction="negative",
            overrides=[
                EventPolicyOverride(
                    relationship_path=("DIRECT_ENTITY",),
                    base_score=0.7,
                    rationale=(
                        "For a negative `capex_cut`, the model treats direct "
                        "company and closely linked holdings exposure as the most "
                        "immediate read-through."
                    ),
                ),
                EventPolicyOverride(
                    relationship_path=("SUPPLIES_TO_AFFECTED",),
                    base_score=0.62,
                    timing_window="immediate",
                    rationale=(
                        "For a negative `capex_cut`, upstream suppliers can react "
                        "quickly because lower spending often hits equipment and "
                        "input demand first."
                    ),
                ),
                EventPolicyOverride(
                    relationship_path=("HOLDS",),
                    base_score=0.5,
                    rationale=(
                        "For a negative `capex_cut`, the model treats direct "
                        "company and closely linked holdings exposure as the most "
                        "immediate read-through."
                    ),
                ),
                EventPolicyOverride(
                    relationship_path=("SUPPLIES_TO_CUSTOMER",),
                    base_score=0.34,
                    rationale=(
                        "For a negative `capex_cut`, downstream customers are "
                        "usually a second-order effect rather than the first "
                        "transmission path."
                    ),
                ),
                EventPolicyOverride(
                    relationship_path=("SUPPLIES_TO_AFFECTED", "HOLDS"),
                    base_score=0.4,
                    rationale=(
                        "For a negative `capex_cut`, upstream suppliers can react "
                        "quickly because lower spending often hits equipment and "
                        "input demand first."
                    ),
                ),
                EventPolicyOverride(
                    relationship_path=("SUPPLIES_TO_CUSTOMER", "HOLDS"),
                    base_score=0.24,
                    rationale=(
                        "For a negative `capex_cut`, downstream customers are "
                        "usually a second-order effect rather than the first "
                        "transmission path."
                    ),
                ),
            ],
        ),
        EventPolicy(
            event_type="supplier_disruption",
            direction="negative",
            overrides=[
                EventPolicyOverride(
                    relationship_path=("SUPPLIES_TO_CUSTOMER",),
                    timing_window="immediate",
                    rationale=(
                        "For a negative `supplier_disruption`, downstream customers "
                        "often react quickly because their shipment risk is immediate."
                    ),
                )
            ],
            fallback_rationale=(
                "For a negative `supplier_disruption`, the model favors "
                "instruments that transmit the supply shock quickly."
            ),
        ),
    ],
)


def get_scoring_policy() -> ScoringPolicy:
    return _DEFAULT_SCORING_POLICY
