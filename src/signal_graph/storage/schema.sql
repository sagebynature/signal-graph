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

CREATE TABLE IF NOT EXISTS journal_signals (
    signal_id TEXT PRIMARY KEY,
    origin_type TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_url TEXT,
    source_ref TEXT,
    raw_text TEXT NOT NULL,
    raw_payload TEXT,
    content_hash TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    observed_at TEXT,
    published_at TEXT,
    agent_host TEXT,
    agent_process TEXT,
    agent_runtime TEXT,
    agent_session_id TEXT,
    agent_role TEXT,
    workspace_path TEXT,
    intent_status TEXT NOT NULL,
    why_text TEXT,
    who_refs TEXT NOT NULL,
    what_refs TEXT NOT NULL,
    where_refs TEXT NOT NULL,
    how_refs TEXT NOT NULL,
    graph_path TEXT NOT NULL,
    journaled_at TEXT
);

CREATE TABLE IF NOT EXISTS recall_artifacts (
    artifact_id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    signal_ids TEXT NOT NULL,
    markdown_text TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    graph_paths TEXT NOT NULL,
    provenance_contract TEXT NOT NULL,
    created_at TEXT NOT NULL
);

COMMIT;
