from __future__ import annotations

import json

import typer

from signal_graph.services.rank import rank_event


def rank(
    event: str = typer.Option(
        ...,
        "--event",
        help="Graph event id to rank candidates for.",
    ),
) -> None:
    ranked_candidates = rank_event(event)
    print(
        json.dumps(
            [candidate.model_dump(mode="json") for candidate in ranked_candidates]
        )
    )
