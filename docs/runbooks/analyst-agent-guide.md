# Analyst And Agent Guide

This guide is for discretionary analysts and coding agents using the CLI as an operating workflow rather than extending the codebase.

## Operating Principle

Use the CLI in a strict pipeline order so every downstream step has stored local state to work from:

`fetch` or `submit` -> `normalize` -> `research` -> `ingest` -> `rank` -> `explain`

Do not skip `research`. It is the provenance gate for downstream graph and memo steps.

## When To Use Which Entry Point

- Use `submit` when a human or agent is manually capturing an event hypothesis
- Use `fetch` when a connector can return raw source items
- Use `normalize` to convert raw source text into a canonical event candidate
- Use `research` to attach supporting evidence, contradictions, and confidence context
- Use `ingest` when the event is ready for graph-oriented reasoning
- Use `rank` to get candidate instruments and timing windows
- Use `explain` to write a memo with clear provenance boundaries

## Standard Manual Workflow

```bash
cat > bundle.json <<'JSON'
{
  "supporting_documents": ["https://example.com/tsmc-capex"],
  "contradictions": ["Demand recovery may offset the capex cut."],
  "entity_resolution_results": {"TSMC": "company:TSMC"},
  "evidence_spans": ["TSMC said it would reduce capital spending."],
  "research_confidence": 0.7,
  "research_notes": "Capex cuts often pressure semiconductor equipment demand."
}
JSON
uv run signal-graph init
uv run python - <<'PY'
from signal_graph.graph.client import GraphClient
from signal_graph.graph.schema import demo_reference_graph_statements

client = GraphClient()
try:
    client.run_in_transaction(demo_reference_graph_statements())
finally:
    client.close()
PY
raw_item_id=$(uv run signal-graph submit --text "TSMC cuts capex" | uv run python -c 'import json,sys; print(json.load(sys.stdin)["raw_item_id"])')
event_candidate_id=$(uv run signal-graph normalize --raw-item "$raw_item_id" --event-type capex_cut --direction negative --primary-entity TSMC | uv run python -c 'import json,sys; print(json.load(sys.stdin)["event_candidate_id"])')
uv run signal-graph research --event-candidate "$event_candidate_id" --bundle-file bundle.json
graph_event_id=$(uv run signal-graph ingest --event-candidate "$event_candidate_id" | uv run python -c 'import json,sys; print(json.load(sys.stdin)["graph_event_id"])')
uv run signal-graph rank --event "$graph_event_id"
uv run signal-graph explain --event "$graph_event_id" --candidate SMH
```

The reference graph load step is explicit. Rank output is limited to instruments already loaded into Neo4j.

## Standard Public Web Workflow

`fetch --source web` is currently a demo stub. It persists a deterministic placeholder item from `example.com`; it is useful for workflow testing, not for live research.

```bash
cat > bundle.json <<'JSON'
{
  "supporting_documents": ["https://example.com/export-control"],
  "contradictions": ["Scope could narrow before enforcement."],
  "entity_resolution_results": {"NVDA": "company:NVDA"},
  "evidence_spans": ["Officials said additional export controls are under review."],
  "research_confidence": 0.6,
  "research_notes": "ETF spillover matters more than fabricated source text in this stub flow."
}
JSON
uv run signal-graph init
uv run python - <<'PY'
from signal_graph.graph.client import GraphClient
from signal_graph.graph.schema import demo_reference_graph_statements

client = GraphClient()
try:
    client.run_in_transaction(demo_reference_graph_statements())
finally:
    client.close()
PY
raw_item_id=$(uv run signal-graph fetch --source web --query "chip export restriction" | uv run python -c 'import json,sys; items=json.load(sys.stdin); print(items[0]["raw_item_id"])')
event_candidate_id=$(uv run signal-graph normalize --raw-item "$raw_item_id" --event-type export_control --direction negative --primary-entity NVDA | uv run python -c 'import json,sys; print(json.load(sys.stdin)["event_candidate_id"])')
uv run signal-graph research --event-candidate "$event_candidate_id" --bundle-file bundle.json
graph_event_id=$(uv run signal-graph ingest --event-candidate "$event_candidate_id" | uv run python -c 'import json,sys; print(json.load(sys.stdin)["graph_event_id"])')
uv run signal-graph rank --event "$graph_event_id"
uv run signal-graph explain --event "$graph_event_id" --candidate SMH
```

`fetch --source premium` is a placeholder today and returns no items until implemented.

## Research Bundle Shape

`research` reads a JSON file matching the current bundle schema:

```json
{
  "supporting_documents": ["https://example.com/tsmc-capex"],
  "contradictions": ["Demand recovery may offset the capex cut."],
  "entity_resolution_results": {"TSMC": "company:TSMC"},
  "evidence_spans": ["TSMC said it would reduce capital spending."],
  "research_confidence": 0.7,
  "research_notes": "Capex cuts often pressure semiconductor equipment demand."
}
```

Use `--allow-empty` only when you deliberately want an empty provenance shell. Normal operation should provide a bundle file.

## Provenance Rules

- Never claim a causal path without stored provenance and supporting source records
- Separate confirmed fact, graph implication, and assistant inference in written output
- Prefer already ingested local events before fetching new data
- Treat contradictions as part of the research record, not as noise to hide
- Avoid presenting ranking output as trading advice; it is decision-support input

## Local Policy Overrides

Operators can change ranking and memo behavior through `.signal-graph/config.toml` under `[scoring_policy]`.

What this can change:

- rank order
- timing windows
- reason-summary wording
- memo rationale text

Coding agents should report when non-default local scoring policy is active, because the same event can rank differently across environments.

Reference example:

- `docs/examples/scoring-policy.example.toml`

## Expected Outputs

- `submit` returns persisted raw-source-item JSON with a stable `raw_item_id`
- `fetch` returns a list of persisted raw-source-item JSON objects; `web` is demo output today and `premium` is placeholder-only
- `normalize` returns an event candidate and supports `--event-type`, `--direction`, `--primary-entity`, and `--secondary-entity`
- `research` returns a persisted research bundle keyed as `rb-<event_candidate_id>`
- `ingest` writes the event, research bundle, source items, and resolved entities into Neo4j and returns a graph event record
- `rank` returns JSON ranked instrument candidates with `instrument_id`, `asset_kind`, scores, timing windows, matched entity, relationship path, and reason summary
- `explain` prints memo text, uses stored evidence and graph paths, and writes a markdown artifact under `.signal-graph/artifacts/`

## What Coding Agents Should Assume

- The CLI is the contract; use explicit commands instead of poking the database directly
- Local state lives under `.signal-graph/`
- SQLite is the source of truth for pipeline progress and provenance artifacts in this MVP
- Neo4j is the reasoning layer, not the system of record for every object
- The demo ranking universe is intentionally small unless you load more instrument reference data
- When in doubt, favor deterministic local behavior over implicit network activity
