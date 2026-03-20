from __future__ import annotations


def classify_timing(
    relationship_types: list[str],
    event_type: str = "",
    direction: str = "",
) -> str:
    if any(
        relationship_type in relationship_types
        for relationship_type in ("DIRECT_ENTITY", "MEMBER_OF", "HOLDS")
    ):
        return "immediate"

    if (
        event_type == "supplier_disruption"
        and direction == "negative"
        and "SUPPLIES_TO_CUSTOMER" in relationship_types
    ):
        return "immediate"

    if (
        event_type == "capex_cut"
        and direction == "negative"
        and "SUPPLIES_TO_AFFECTED" in relationship_types
    ):
        return "immediate"

    return "short_drift"
