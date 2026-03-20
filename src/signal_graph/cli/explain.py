from __future__ import annotations

import typer

from signal_graph.config import DEFAULT_PROJECT_DIR
from signal_graph.services.explain import write_memo_artifact


def explain(
    event: str = typer.Option(
        ...,
        "--event",
        help="Graph event id to explain.",
    ),
    candidate: str = typer.Option(
        ...,
        "--candidate",
        help="Candidate ticker symbol to explain.",
    ),
) -> None:
    memo = write_memo_artifact(DEFAULT_PROJECT_DIR / "artifacts", event, candidate)
    print(memo.memo_text)
