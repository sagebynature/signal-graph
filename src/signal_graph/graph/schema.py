from __future__ import annotations

SCHEMA_CONSTRAINTS = [
    "CREATE CONSTRAINT company_ticker IF NOT EXISTS FOR (c:Company) REQUIRE c.ticker IS UNIQUE",
]


def graph_event_query() -> str:
    return (
        "MERGE (e:Event {event_candidate_id: $event_candidate_id}) "
        "SET e.research_bundle_id = $research_bundle_id"
    )
