from __future__ import annotations

from signal_graph.services.scoring_policy import get_scoring_policy


def classify_timing(
    relationship_types: list[str],
    event_type: str = "",
    direction: str = "",
) -> str:
    resolved_policy = get_scoring_policy().resolve(
        relationship_types,
        event_type=event_type,
        direction=direction,
    )
    return resolved_policy.timing_window
