from __future__ import annotations

from pathlib import Path

from trade_graph.models.graph import MemoResponse


def explain_candidate(graph_event_id: str, ticker: str) -> str:
    return "\n".join(
        [
            "Confirmed fact: Event was ingested from stored sources.",
            "Graph implication: Candidate is linked via stored relationship paths.",
            "Assistant inference: Timing window is immediate.",
        ]
    )


def write_memo_artifact(artifact_dir: Path, graph_event_id: str, ticker: str) -> MemoResponse:
    memo_text = explain_candidate(graph_event_id, ticker)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / f"{graph_event_id}-{ticker}.md"
    artifact_path.write_text(memo_text)
    return MemoResponse(
        graph_event_id=graph_event_id,
        ticker=ticker,
        memo_text=memo_text,
        artifact_path=str(artifact_path),
    )
