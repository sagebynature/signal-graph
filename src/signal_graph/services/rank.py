from __future__ import annotations

from typing import Any

from signal_graph.config import DEFAULT_PROJECT_DIR
from signal_graph.graph.client import GraphClient
from signal_graph.models.graph import GraphEvent, RankedCandidate
from signal_graph.models.research import ResearchBundle
from signal_graph.services.scoring_policy import get_scoring_policy
from signal_graph.storage.sqlite import SqliteStore


def _candidate_rows_query() -> str:
    return (
        "MATCH (e:Event {event_candidate_id: $event_candidate_id}) "
        "MATCH (e)-[:AFFECTS|IMPACTS]->(company:Company) "
        "WITH e, company "
        "CALL (company) { "
        "    WITH company "
        "    RETURN company.ticker AS ticker, company.ticker AS matched_entity, ['DIRECT_ENTITY'] AS relationship_path, 0 AS path_length "
        "    UNION "
        "    WITH company "
        "    MATCH (instrument:Instrument)-[:HOLDS]->(company) "
        "    RETURN instrument.ticker AS ticker, company.ticker AS matched_entity, ['HOLDS'] AS relationship_path, 1 AS path_length "
        "    UNION "
        "    WITH company "
        "    MATCH (company)-[:SUPPLIES]->(downstream:Company) "
        "    RETURN downstream.ticker AS ticker, company.ticker AS matched_entity, ['SUPPLIES_TO_CUSTOMER'] AS relationship_path, 1 AS path_length "
        "    UNION "
        "    WITH company "
        "    MATCH (company)-[:SUPPLIES]->(downstream:Company)<-[:HOLDS]-(instrument:Instrument) "
        "    RETURN instrument.ticker AS ticker, company.ticker AS matched_entity, ['SUPPLIES_TO_CUSTOMER', 'HOLDS'] AS relationship_path, 2 AS path_length "
        "    UNION "
        "    WITH company "
        "    MATCH (upstream:Company)-[:SUPPLIES]->(company) "
        "    RETURN upstream.ticker AS ticker, company.ticker AS matched_entity, ['SUPPLIES_TO_AFFECTED'] AS relationship_path, 1 AS path_length "
        "    UNION "
        "    WITH company "
        "    MATCH (upstream:Company)-[:SUPPLIES]->(company)<-[:HOLDS]-(instrument:Instrument) "
        "    RETURN instrument.ticker AS ticker, company.ticker AS matched_entity, ['SUPPLIES_TO_AFFECTED', 'HOLDS'] AS relationship_path, 2 AS path_length "
        "} "
        "RETURN ticker, matched_entity, relationship_path, path_length, "
        "       e.event_type AS event_type, "
        "       e.direction AS direction"
    )


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, round(value, 2)))


def _resolve_research_bundle(
    store: SqliteStore, graph_event: GraphEvent
) -> ResearchBundle:
    if graph_event.research_bundle_id:
        bundle = store.get_research_bundle_by_id(graph_event.research_bundle_id)
        if bundle is None:
            raise ValueError(
                f"research bundle not found: {graph_event.research_bundle_id}"
            )
        return bundle

    bundle = store.get_latest_research_bundle(graph_event.event_candidate_id)
    if bundle is None:
        raise ValueError(f"research bundle not found: {graph_event.event_candidate_id}")
    return bundle


def _resolve_scoring_policy(bundle: ResearchBundle):
    return bundle.scoring_policy_snapshot or get_scoring_policy()


def _score_candidate(
    row: dict[str, Any], *, research_bundle: ResearchBundle
) -> RankedCandidate:
    relationship_path = list(row["relationship_path"])
    path_length = int(row["path_length"])
    event_type = str(row.get("event_type", ""))
    direction = str(row.get("direction", ""))

    resolved_policy = _resolve_scoring_policy(research_bundle).resolve(
        relationship_path,
        event_type=event_type,
        direction=direction,
    )
    base_score = resolved_policy.base_score
    research_confidence = research_bundle.research_confidence
    support_count = len(research_bundle.supporting_documents)
    evidence_count = len(research_bundle.evidence_spans)
    contradiction_count = len(research_bundle.contradictions)

    evidence_bonus = min(
        0.25,
        (research_confidence * 0.2) + (support_count * 0.05) + (evidence_count * 0.03),
    )
    contradiction_penalty = min(0.15, contradiction_count * 0.05)
    fast_reaction_score = _clamp_score(
        base_score + evidence_bonus - contradiction_penalty
    )
    follow_through_score = _clamp_score(
        fast_reaction_score - 0.1 + (0.05 if path_length > 0 else 0.0)
    )

    return RankedCandidate(
        ticker=str(row["ticker"]),
        fast_reaction_score=fast_reaction_score,
        follow_through_score=follow_through_score,
        timing_window=resolved_policy.timing_window,
        matched_entity=str(row["matched_entity"]),
        relationship_path=relationship_path,
        reason_summary=(
            f"{row['ticker']} is exposed to {row['matched_entity']} via "
            f"{resolved_policy.description}"
        ),
    )


def rank_event(graph_event_id: str) -> list[RankedCandidate]:
    store = SqliteStore(DEFAULT_PROJECT_DIR / "signal_graph.db")
    graph_event = store.get_graph_event(graph_event_id)
    if graph_event is None:
        raise ValueError(f"graph event not found: {graph_event_id}")
    research_bundle = _resolve_research_bundle(store, graph_event)

    client = GraphClient()
    try:
        rows = client.run(
            _candidate_rows_query(),
            {"event_candidate_id": graph_event.event_candidate_id},
        )
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()

    ranked_by_ticker: dict[str, RankedCandidate] = {}
    for row in rows:
        candidate = _score_candidate(row, research_bundle=research_bundle)
        existing = ranked_by_ticker.get(candidate.ticker)
        if (
            existing is None
            or candidate.fast_reaction_score > existing.fast_reaction_score
        ):
            ranked_by_ticker[candidate.ticker] = candidate

    return sorted(
        ranked_by_ticker.values(),
        key=lambda candidate: (
            candidate.fast_reaction_score,
            candidate.follow_through_score,
        ),
        reverse=True,
    )
