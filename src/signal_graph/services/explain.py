from __future__ import annotations

from pathlib import Path

from signal_graph.config import DEFAULT_PROJECT_DIR
from signal_graph.models.graph import MemoResponse
from signal_graph.services.rank import (
    rank_event,
    _resolve_research_bundle,
    _resolve_scoring_policy,
)
from signal_graph.storage.sqlite import SqliteStore


def explain_candidate(
    graph_event_id: str, ticker: str, *, ranked_candidates=None
) -> str:
    store = SqliteStore(DEFAULT_PROJECT_DIR / "signal_graph.db")
    graph_event = store.get_graph_event(graph_event_id)
    if graph_event is None:
        raise ValueError(f"graph event not found: {graph_event_id}")

    event_candidate = store.get_event_candidate(graph_event.event_candidate_id)
    if event_candidate is None:
        raise ValueError(f"event candidate not found: {graph_event.event_candidate_id}")

    research_bundle = _resolve_research_bundle(store, graph_event)

    source_items = [
        store.get_raw_source_item(raw_item_id)
        for raw_item_id in event_candidate.source_item_ids
    ]
    source_texts = [item.raw_text for item in source_items if item is not None]
    supporting_documents = ", ".join(research_bundle.supporting_documents) or "none"
    contradictions = (
        "; ".join(research_bundle.contradictions)
        if research_bundle.contradictions
        else "none recorded"
    )

    ranked_candidates = (
        rank_event(graph_event_id) if ranked_candidates is None else ranked_candidates
    )
    ranked_candidate = next(
        (candidate for candidate in ranked_candidates if candidate.ticker == ticker),
        None,
    )
    if ranked_candidate is None:
        raise ValueError(f"ranked candidate not found: {ticker}")

    resolved_policy = _resolve_scoring_policy(research_bundle).resolve(
        ranked_candidate.relationship_path,
        event_type=event_candidate.event_type,
        direction=event_candidate.direction,
    )

    return "\n".join(
        [
            (
                f"Confirmed fact: Event `{event_candidate.title}` is stored as "
                f"`{event_candidate.event_type}` with `{event_candidate.direction}` direction "
                f"from {len(source_texts)} source item(s)."
            ),
            f"Confirmed fact: Supporting documents: {supporting_documents}.",
            f"Confirmed fact: Evidence spans: {'; '.join(research_bundle.evidence_spans) or 'none recorded'}.",
            (
                f"Graph implication: Candidate `{ticker}` is linked to `{ranked_candidate.matched_entity}` "
                f"via {resolved_policy.description}."
            ),
            (
                f"Graph implication: Reason summary: {ranked_candidate.reason_summary}. "
                f"Research confidence is {research_bundle.research_confidence:.2f}."
            ),
            *(
                [f"Graph implication: {resolved_policy.rationale}"]
                if resolved_policy.rationale
                else []
            ),
            (
                f"Assistant inference: `{ticker}` scores fast_reaction={ranked_candidate.fast_reaction_score:.2f} "
                f"and follow_through={ranked_candidate.follow_through_score:.2f}, suggesting an "
                f"`{ranked_candidate.timing_window}` reaction window."
            ),
            f"Assistant inference: Contradictions to weigh: {contradictions}.",
        ]
    )


def write_memo_artifact(
    artifact_dir: Path, graph_event_id: str, ticker: str
) -> MemoResponse:
    ranked_candidates = rank_event(graph_event_id)
    memo_text = explain_candidate(
        graph_event_id, ticker, ranked_candidates=ranked_candidates
    )
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / f"{graph_event_id}-{ticker}.md"
    artifact_path.write_text(memo_text)
    return MemoResponse(
        graph_event_id=graph_event_id,
        ticker=ticker,
        memo_text=memo_text,
        artifact_path=str(artifact_path),
        ranked_candidates=ranked_candidates,
    )
