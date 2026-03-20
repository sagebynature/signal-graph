from __future__ import annotations

import typer

from trade_graph.services.rank import rank_event


def rank(event: str = typer.Option(..., "--event")) -> None:
    ranked_candidates = rank_event(event)
    print([candidate.model_dump(mode="json") for candidate in ranked_candidates])
