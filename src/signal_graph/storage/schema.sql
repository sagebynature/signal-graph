BEGIN;

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
    view TEXT NOT NULL DEFAULT 'ranked',
    query_contract TEXT,
    matches TEXT NOT NULL DEFAULT '[]',
    session_groups TEXT NOT NULL DEFAULT '[]',
    markdown_text TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    graph_paths TEXT NOT NULL,
    provenance_contract TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_journal_signals_captured_at
    ON journal_signals(captured_at DESC);

CREATE INDEX IF NOT EXISTS idx_journal_signals_session_id
    ON journal_signals(agent_session_id);

COMMIT;
