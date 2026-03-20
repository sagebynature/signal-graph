from __future__ import annotations


def classify_timing(relationship_types: list[str]) -> str:
    if any(
        relationship_type in relationship_types
        for relationship_type in ("DIRECT_ENTITY", "MEMBER_OF", "HOLDS")
    ):
        return "immediate"
    return "short_drift"
