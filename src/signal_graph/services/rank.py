from __future__ import annotations

from typing import Any

from signal_graph.config import DEFAULT_PROJECT_DIR
from signal_graph.graph.client import GraphClient
from signal_graph.models.graph import RankedCandidate
from signal_graph.services.timing import classify_timing
from signal_graph.storage.sqlite import SqliteStore

DEFAULT_PATH_BASE_SCORES: dict[tuple[str, ...], float] = {
    ("DIRECT_ENTITY",): 0.7,
    ("SUPPLIES_TO_CUSTOMER",): 0.58,
    ("HOLDS",): 0.5,
    ("SUPPLIES_TO_AFFECTED",): 0.44,
    ("SUPPLIES_TO_CUSTOMER", "HOLDS"): 0.38,
    ("SUPPLIES_TO_AFFECTED", "HOLDS"): 0.32,
}

EVENT_PATH_BASE_SCORES: dict[tuple[str, str], dict[tuple[str, ...], float]] = {
    (
        "capex_cut",
        "negative",
    ): {
        ("DIRECT_ENTITY",): 0.7,
        ("SUPPLIES_TO_AFFECTED",): 0.62,
        ("HOLDS",): 0.5,
        ("SUPPLIES_TO_CUSTOMER",): 0.34,
        ("SUPPLIES_TO_AFFECTED", "HOLDS"): 0.4,
        ("SUPPLIES_TO_CUSTOMER", "HOLDS"): 0.24,
    }
}


def _candidate_rows_query() -> str:
    return (
        "MATCH (e:Event {event_candidate_id: $event_candidate_id})-[:HAS_RESEARCH]->(rb:ResearchBundle) "
        "MATCH (e)-[:AFFECTS|IMPACTS]->(company:Company) "
        "WITH e, rb, company, "
        "     COUNT { (rb)-[:SUPPORTS]->(:Document) } AS support_count, "
        "     COUNT { (rb)-[:HAS_EVIDENCE]->(:EvidenceSpan) } AS evidence_count, "
        "     COUNT { (rb)-[:CONTRADICTED_BY]->(:Claim) } AS contradiction_count "
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
        "       e.direction AS direction, "
        "       toFloat(rb.research_confidence) AS research_confidence, "
        "       support_count, evidence_count, contradiction_count"
    )


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, round(value, 2)))


def _base_score(event_type: str, direction: str, relationship_path: list[str]) -> float:
    event_overrides = EVENT_PATH_BASE_SCORES.get((event_type, direction), {})
    return event_overrides.get(
        tuple(relationship_path),
        DEFAULT_PATH_BASE_SCORES.get(tuple(relationship_path), 0.32),
    )


def _score_candidate(row: dict[str, Any]) -> RankedCandidate:
    relationship_path = list(row["relationship_path"])
    path_length = int(row["path_length"])
    event_type = str(row.get("event_type", ""))
    direction = str(row.get("direction", ""))
    research_confidence = float(row["research_confidence"])
    support_count = int(row["support_count"])
    evidence_count = int(row["evidence_count"])
    contradiction_count = int(row["contradiction_count"])

    base_score = _base_score(event_type, direction, relationship_path)

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
        timing_window=classify_timing(relationship_path, event_type, direction),
        matched_entity=str(row["matched_entity"]),
        relationship_path=relationship_path,
        reason_summary=(
            f"{row['ticker']} is exposed to {row['matched_entity']} via "
            f"{' -> '.join(relationship_path)}"
        ),
    )


def rank_event(graph_event_id: str) -> list[RankedCandidate]:
    store = SqliteStore(DEFAULT_PROJECT_DIR / "signal_graph.db")
    graph_event = store.get_graph_event(graph_event_id)
    if graph_event is None:
        raise ValueError(f"graph event not found: {graph_event_id}")

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
        candidate = _score_candidate(row)
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
