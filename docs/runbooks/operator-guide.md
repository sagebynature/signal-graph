# Operator Guide

This guide is for developers and local operators working inside the repository.

## Environment

- Python 3.12
- `uv` for dependency and command execution
- `ty` for contributor type checks
- Docker for the local Neo4j runtime
- `make` for common workflows

## Bootstrap

```bash
uv sync
uv run signal-graph doctor
uv run signal-graph init
uv run signal-graph version
```

`signal-graph doctor` is non-destructive. It validates runtime readiness for the local workflow, confirms `.signal-graph/config.toml` is parseable when present, and rejects malformed `NEO4J_AUTH` values. The config file itself is optional.

## Neo4j Runtime

Before first startup, set `NEO4J_AUTH` if you do not want the default `neo4j/<password>` credential.

```bash
make neo4j-up
docker compose ps
make neo4j-down
```

Operational notes:

- wait for the container to become `healthy` before connecting
- `./infra/neo4j/data` holds persisted database state
- removing `./infra/neo4j/data` also removes local graph state
- `NEO4J_AUTH` must use the `username/password` format with non-empty values
- if you change `NEO4J_AUTH`, you may need to clear `./infra/neo4j/data` or keep using the existing password
- runtime config is loaded from `.signal-graph/config.toml` when present and can be overridden with `NEO4J_URI`, `NEO4J_AUTH`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, and `NEO4J_DATABASE`
- `signal-graph doctor` reports malformed or unreadable config explicitly; other commands that load runtime config currently raise an error when they encounter invalid config

## Scoring Policy Config

Scoring policy overrides live in `.signal-graph/config.toml` under `[scoring_policy]`. The file is optional, but if it exists it must be valid TOML. The merge order is:

1. built-in defaults from the repo
2. local path overrides matched by `relationship_path`
3. local event overrides matched by `event_type + direction + relationship_path`

Malformed scoring policy config is not ignored. `signal-graph doctor` reports it explicitly, and commands that load config currently raise a `ValueError`.

Reference example:

- `docs/examples/scoring-policy.example.toml`

Example: make negative `capex_cut` events more punitive for upstream suppliers.

```toml
[scoring_policy]

[[scoring_policy.events]]
event_type = "capex_cut"
direction = "negative"

[[scoring_policy.events.overrides]]
relationship_path = ["SUPPLIES_TO_AFFECTED"]
base_score = 0.62
timing_window = "immediate"
rationale = "For a negative `capex_cut`, upstream suppliers can react quickly because lower spending often hits equipment and input demand first."
```

Example: add a new `export_control` policy that boosts ETF spillover.

```toml
[scoring_policy]

[[scoring_policy.events]]
event_type = "export_control"
direction = "negative"
fallback_rationale = "For a negative `export_control`, the model emphasizes instruments that move with immediate market access risk."

[[scoring_policy.events.overrides]]
relationship_path = ["HOLDS"]
base_score = 0.64
timing_window = "immediate"
rationale = "For a negative `export_control`, sector ETF exposure can move immediately."
```

## Common Verification Commands

```bash
uv run python -m pytest -v
uv run ty check
uv run signal-graph doctor
uv run signal-graph version
```

`uv run ty check` is for contributors. `signal-graph doctor` only requires runtime tooling.

## Manual Smoke Test

The full copy-pasteable smoke flow lives in [`docs/runbooks/runnable-smoke-test.md`](runnable-smoke-test.md). It uses command substitution to capture real ids, keeps `.signal-graph/` state in a fresh temp directory, and explicitly seeds the demo reference graph before ranking.

If you want the short form from the repo root:

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

Expected behavior:

- `fetch --source web` returns deterministic demo output today; it is not live web retrieval
- `fetch --source premium` is currently disabled and exits with a clear placeholder message
- `research` fails on an empty bundle unless `--allow-empty` is set
- `ingest` updates the event graph transactionally but does not seed demo instruments automatically
- `rank` returns JSON instrument candidates with `instrument_id`, `asset_kind`, `relationship_path`, and `reason_summary`
- `rank` is only as broad as the instrument reference data already loaded into Neo4j
- `explain` writes a markdown memo under `.signal-graph/artifacts/`
- local scoring policy config can change rank order, timing windows, path descriptions, and memo rationale without code edits

## Repository Responsibilities

- `src/signal_graph/cli/`: CLI entrypoints and command surface
- `src/signal_graph/services/`: pipeline logic
- `src/signal_graph/models/`: canonical data models
- `src/signal_graph/storage/`: local SQLite access and schema
- `src/signal_graph/graph/`: graph client and schema helpers
- `tests/`: CLI, storage, docs, and end-to-end verification

## Troubleshooting

- `signal-graph doctor` fails: read the reported config or `NEO4J_AUTH` error first, then install any missing runtime tooling before debugging application code
- Neo4j auth mismatch: either keep the existing password or reset the local data directory
- Unexpected local state: inspect `.signal-graph/signal_graph.db` and `.signal-graph/artifacts/`
- Rank output looks empty or weak: confirm your normalized event has `--primary-entity` data and that tradable instrument reference data has been loaded into Neo4j
- `fetch --source web` looks fake: that is expected today; it returns deterministic stub content from `example.com`
- `fetch --source premium` exits immediately: that is expected until a real premium connector is implemented
- Rank or memo behavior changed unexpectedly: inspect `.signal-graph/config.toml` and compare it with `docs/examples/scoring-policy.example.toml`
- Smoke test drift: run `uv run python -m pytest -v` first, then reproduce the failing CLI step manually
