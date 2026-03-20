from __future__ import annotations

from signal_graph.models.graph import RankedCandidate
from signal_graph.services.timing import classify_timing


def rank_event(graph_event_id: str) -> list[RankedCandidate]:
    return [
        RankedCandidate(
            ticker="SMH",
            fast_reaction_score=0.75,
            follow_through_score=0.40,
            timing_window=classify_timing(["MEMBER_OF"]),
        )
    ]
