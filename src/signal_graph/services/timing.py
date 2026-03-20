from __future__ import annotations


def classify_timing(relationship_types: list[str]) -> str:
    if "MEMBER_OF" in relationship_types:
        return "immediate"
    return "short_drift"
