from __future__ import annotations

from pathlib import Path

from signal_graph.config import DEFAULT_PROJECT_DIR
from signal_graph.models.graph import MemoResponse
from signal_graph.services.rank import rank_event
from signal_graph.storage.sqlite import SqliteStore


def _describe_relationship_path(relationship_path: list[str]) -> str:
    path_descriptions: dict[tuple[str, ...], str] = {
        ("DIRECT_ENTITY",): "direct company exposure",
        ("HOLDS",): "ETF holding exposure",
        ("SUPPLIES_TO_CUSTOMER",): "downstream customer spillover",
        ("SUPPLIES_TO_AFFECTED",): "upstream supplier exposure",
        (
            "SUPPLIES_TO_CUSTOMER",
            "HOLDS",
        ): "ETF exposure to downstream customer spillover",
        ("SUPPLIES_TO_AFFECTED", "HOLDS"): "ETF exposure to upstream supplier pressure",
    }
    return path_descriptions.get(
        tuple(relationship_path), "graph relationship exposure"
    )


def _event_rationale(
    event_type: str, direction: str, relationship_path: list[str]
) -> str | None:
    if event_type == "capex_cut" and direction == "negative":
        if "SUPPLIES_TO_AFFECTED" in relationship_path:
            return (
                "For a negative `capex_cut`, upstream suppliers can react quickly "
                "because lower spending often hits equipment and input demand first."
            )
        if "SUPPLIES_TO_CUSTOMER" in relationship_path:
            return (
                "For a negative `capex_cut`, downstream customers are usually a "
                "second-order effect rather than the first transmission path."
            )
        return (
            "For a negative `capex_cut`, the model treats direct company and "
            "closely linked holdings exposure as the most immediate read-through."
        )

    if event_type == "supplier_disruption" and direction == "negative":
        if "SUPPLIES_TO_CUSTOMER" in relationship_path:
            return (
                "For a negative `supplier_disruption`, downstream customers often "
                "react quickly because their shipment risk is immediate."
            )
        return (
            "For a negative `supplier_disruption`, the model favors instruments "
            "that transmit the supply shock quickly."
        )

    return None


def explain_candidate(graph_event_id: str, ticker: str) -> str:
    store = SqliteStore(DEFAULT_PROJECT_DIR / "signal_graph.db")
    graph_event = store.get_graph_event(graph_event_id)
    if graph_event is None:
        raise ValueError(f"graph event not found: {graph_event_id}")

    event_candidate = store.get_event_candidate(graph_event.event_candidate_id)
    if event_candidate is None:
        raise ValueError(f"event candidate not found: {graph_event.event_candidate_id}")

    research_bundle = store.get_research_bundle(graph_event.event_candidate_id)
    if research_bundle is None:
        raise ValueError(f"research bundle not found: {graph_event.event_candidate_id}")

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

    ranked_candidates = rank_event(graph_event_id)
    ranked_candidate = next(
        (candidate for candidate in ranked_candidates if candidate.ticker == ticker),
        None,
    )
    if ranked_candidate is None:
        raise ValueError(f"ranked candidate not found: {ticker}")

    path_description = _describe_relationship_path(ranked_candidate.relationship_path)
    rationale = _event_rationale(
        event_candidate.event_type,
        event_candidate.direction,
        ranked_candidate.relationship_path,
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
                f"via {path_description}."
            ),
            (
                f"Graph implication: Reason summary: {ranked_candidate.reason_summary}. "
                f"Research confidence is {research_bundle.research_confidence:.2f}."
            ),
            *([f"Graph implication: {rationale}"] if rationale else []),
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
    memo_text = explain_candidate(graph_event_id, ticker)
    ranked_candidates = rank_event(graph_event_id)
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
