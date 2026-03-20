from __future__ import annotations

import typer

from trade_graph.config import DEFAULT_PROJECT_DIR
from trade_graph.services.explain import write_memo_artifact


def explain(
    event: str = typer.Option(..., "--event"),
    candidate: str = typer.Option(..., "--candidate"),
) -> None:
    memo = write_memo_artifact(DEFAULT_PROJECT_DIR / "artifacts", event, candidate)
    print(memo.memo_text)
