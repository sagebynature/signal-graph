BEGIN;

CREATE TABLE IF NOT EXISTS raw_source_items (
    raw_item_id TEXT PRIMARY KEY,
    source_tier TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_url TEXT,
    fetched_at TEXT,
    published_at TEXT,
    raw_text TEXT NOT NULL,
    raw_payload TEXT
);

CREATE TABLE IF NOT EXISTS event_candidates (
    event_candidate_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    event_type TEXT NOT NULL,
    direction TEXT NOT NULL,
    primary_entities TEXT NOT NULL,
    dedupe_fingerprint TEXT,
    secondary_entities TEXT NOT NULL,
    source_item_ids TEXT NOT NULL,
    candidate_confidence REAL NOT NULL,
    candidate_status TEXT NOT NULL,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS event_candidate_source_items (
    raw_item_id TEXT PRIMARY KEY REFERENCES raw_source_items(raw_item_id) ON DELETE CASCADE,
    event_candidate_id TEXT NOT NULL REFERENCES event_candidates(event_candidate_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS research_bundles (
    research_bundle_id TEXT PRIMARY KEY,
    event_candidate_id TEXT NOT NULL REFERENCES event_candidates(event_candidate_id) ON DELETE CASCADE,
    bundle_revision INTEGER,
    scoring_policy_snapshot TEXT,
    supporting_documents TEXT NOT NULL,
    contradictions TEXT NOT NULL,
    entity_resolution_results TEXT,
    evidence_spans TEXT,
    research_confidence REAL NOT NULL,
    research_notes TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS graph_events (
    graph_event_id TEXT PRIMARY KEY,
    event_candidate_id TEXT NOT NULL REFERENCES event_candidates(event_candidate_id) ON DELETE CASCADE,
    research_bundle_id TEXT REFERENCES research_bundles(research_bundle_id),
    committed_at TEXT NOT NULL,
    trust_score REAL NOT NULL,
    eligible_modes TEXT NOT NULL,
    ingest_decision TEXT NOT NULL
);

COMMIT;
