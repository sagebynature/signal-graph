from __future__ import annotations

SCHEMA_CONSTRAINTS = [
    "CREATE CONSTRAINT company_ticker IF NOT EXISTS FOR (c:Company) REQUIRE c.ticker IS UNIQUE",
    "CREATE CONSTRAINT instrument_ticker IF NOT EXISTS FOR (i:Instrument) REQUIRE i.ticker IS UNIQUE",
    "CREATE CONSTRAINT event_candidate IF NOT EXISTS FOR (e:Event) REQUIRE e.event_candidate_id IS UNIQUE",
    "CREATE CONSTRAINT research_bundle IF NOT EXISTS FOR (rb:ResearchBundle) REQUIRE rb.research_bundle_id IS UNIQUE",
    "CREATE CONSTRAINT source_item IF NOT EXISTS FOR (s:SourceItem) REQUIRE s.raw_item_id IS UNIQUE",
    "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.document_id IS UNIQUE",
]


REFERENCE_GRAPH_QUERIES = [
    "MERGE (c:Company {ticker: 'TSMC'}) SET c.name = 'Taiwan Semiconductor Manufacturing Company'",
    "MERGE (c:Company {ticker: 'NVDA'}) SET c.name = 'NVIDIA'",
    "MERGE (c:Company {ticker: 'AMD'}) SET c.name = 'Advanced Micro Devices'",
    "MERGE (c:Company {ticker: 'ASML'}) SET c.name = 'ASML'",
    "MERGE (c:Company {ticker: 'INTC'}) SET c.name = 'Intel'",
    "MERGE (:Instrument {ticker: 'SMH', kind: 'ETF'})",
    "MERGE (:Instrument {ticker: 'SOXX', kind: 'ETF'})",
    (
        "MATCH (smh:Instrument {ticker: 'SMH'}), (nvda:Company {ticker: 'NVDA'}) "
        "MERGE (smh)-[:HOLDS]->(nvda)"
    ),
    (
        "MATCH (smh:Instrument {ticker: 'SMH'}), (tsmc:Company {ticker: 'TSMC'}) "
        "MERGE (smh)-[:HOLDS]->(tsmc)"
    ),
    (
        "MATCH (soxx:Instrument {ticker: 'SOXX'}), (amd:Company {ticker: 'AMD'}) "
        "MERGE (soxx)-[:HOLDS]->(amd)"
    ),
    (
        "MATCH (tsmc:Company {ticker: 'TSMC'}), (nvda:Company {ticker: 'NVDA'}) "
        "MERGE (tsmc)-[:SUPPLIES]->(nvda)"
    ),
]


def graph_event_query() -> str:
    return (
        "MERGE (e:Event {event_candidate_id: $event_candidate_id}) "
        "SET e.title = $title, "
        "    e.event_type = $event_type, "
        "    e.direction = $direction "
        "MERGE (rb:ResearchBundle {research_bundle_id: $research_bundle_id}) "
        "SET rb.research_confidence = $research_confidence, "
        "    rb.research_notes = $research_notes, "
        "    rb.has_entity_resolution = size(keys($entity_resolution_results)) > 0 "
        "MERGE (e)-[:HAS_RESEARCH]->(rb) "
        "FOREACH (entity IN $primary_entities | "
        "    MERGE (c:Company {ticker: entity}) "
        "    ON CREATE SET c.name = entity "
        "    MERGE (e)-[:AFFECTS]->(c)"
        ") "
        "FOREACH (entity IN $secondary_entities | "
        "    MERGE (c:Company {ticker: entity}) "
        "    ON CREATE SET c.name = entity "
        "    MERGE (e)-[:IMPACTS]->(c)"
        ") "
        "FOREACH (source_item_id IN $source_item_ids | "
        "    MERGE (s:SourceItem {raw_item_id: source_item_id}) "
        "    MERGE (e)-[:DERIVED_FROM]->(s)"
        ") "
        "FOREACH (document_url IN $supporting_documents | "
        "    MERGE (d:Document {document_id: document_url}) "
        "    SET d.url = document_url "
        "    MERGE (rb)-[:SUPPORTS]->(d)"
        ") "
        "FOREACH (claim IN $contradictions | "
        "    MERGE (c:Claim {text: claim}) "
        "    MERGE (rb)-[:CONTRADICTED_BY]->(c)"
        ") "
        "FOREACH (span IN $evidence_spans | "
        "    MERGE (es:EvidenceSpan {text: span}) "
        "    MERGE (rb)-[:HAS_EVIDENCE]->(es)"
        ") "
        "FOREACH (entity_name IN keys($entity_resolution_results) | "
        "    MERGE (resolved:ResolvedEntity {name: entity_name}) "
        "    SET resolved.reference = $entity_resolution_results[entity_name] "
        "    MERGE (rb)-[:RESOLVES]->(resolved)"
        ") "
        "RETURN e.event_candidate_id AS event_candidate_id"
    )


def graph_cleanup_query() -> str:
    return (
        "MATCH (e:Event {event_candidate_id: $event_candidate_id}) "
        "OPTIONAL MATCH (e)-[event_rel:AFFECTS|IMPACTS|DERIVED_FROM|HAS_RESEARCH]->() "
        "DELETE event_rel "
        "WITH e "
        "OPTIONAL MATCH (rb:ResearchBundle {research_bundle_id: $research_bundle_id})-"
        "[research_rel:SUPPORTS|CONTRADICTED_BY|HAS_EVIDENCE|RESOLVES]->() "
        "DELETE research_rel "
        "RETURN e.event_candidate_id AS event_candidate_id"
    )


def graph_event_params(event_candidate, research_bundle) -> dict:
    return {
        "event_candidate_id": event_candidate.event_candidate_id,
        "title": event_candidate.title,
        "event_type": event_candidate.event_type,
        "direction": event_candidate.direction,
        "primary_entities": event_candidate.primary_entities,
        "secondary_entities": event_candidate.secondary_entities,
        "source_item_ids": event_candidate.source_item_ids,
        "research_bundle_id": research_bundle.research_bundle_id,
        "supporting_documents": research_bundle.supporting_documents,
        "contradictions": research_bundle.contradictions,
        "entity_resolution_results": research_bundle.entity_resolution_results or {},
        "evidence_spans": research_bundle.evidence_spans,
        "research_confidence": research_bundle.research_confidence,
        "research_notes": research_bundle.research_notes,
    }
