# Operator Guide

This guide is for developers and local operators running the repository itself.

If you want product context first, read [`../overview/product.md`](../overview/product.md). If you want the research workflow, read [`analyst-agent-guide.md`](analyst-agent-guide.md).

## Prerequisites

- Python 3.12
- `uv` for environment and command execution
- `ty` for type checking
- Docker for Neo4j
- `make` for common repo workflows

## Bootstrap

```bash
uv sync --group dev
uv run signal-graph doctor
uv run signal-graph init
uv run signal-graph version
```

Notes:

- `signal-graph doctor` exits non-zero only when required tooling is missing.
- `config: missing` is expected until you create `.signal-graph/config.toml`.
- `signal-graph init` creates `.signal-graph/`, `.signal-graph/cache/`, `.signal-graph/artifacts/`, and `.signal-graph/signal_graph.db`.

## Local State Layout

Important local paths:

- `.signal-graph/signal_graph.db`: SQLite system of record
- `.signal-graph/artifacts/`: generated memo artifacts
- `.signal-graph/cache/`: local cache directory
- `.signal-graph/config.toml`: optional local config overrides
- `infra/neo4j/data`: persisted Neo4j state
- `infra/neo4j/logs`: Neo4j logs
- `infra/neo4j/plugins`: Neo4j plugins

## Neo4j Runtime

Before first startup, set `NEO4J_AUTH` if you do not want the default `neo4j/password` credential.

```bash
make neo4j-up
docker compose ps
make neo4j-down
```

Operational notes:

- Wait for the container to become `healthy` before using graph-backed commands.
- If you change `NEO4J_AUTH`, you may need to clear `infra/neo4j/data` or keep using the existing password.
- Removing `infra/neo4j/data` also removes local graph state.
- Runtime config can come from `.signal-graph/config.toml` and can be overridden with `NEO4J_URI`, `NEO4J_AUTH`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, and `NEO4J_DATABASE`.

## Local Config

The optional `.signal-graph/config.toml` file has two practical uses in this cut:

- Neo4j connection settings
- scoring-policy overrides

Reference example:

- [`../examples/scoring-policy.example.toml`](../examples/scoring-policy.example.toml)

## Scoring Policy Overrides

Scoring policy overrides live under `[scoring_policy]`.

Merge order:

1. Built-in defaults from the repo
2. Local path overrides matched by `relationship_path`
3. Local event overrides matched by `event_type + direction + relationship_path`

Malformed scoring policy config fails fast. It is not ignored.

Example: make negative `capex_cut` events harsher on upstream suppliers.

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

Example: add an `export_control` rule that boosts ETF spillover.

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

## Manual Smoke Test

The commands below use placeholder IDs. Replace them with the values returned by the previous command.

```bash
uv run signal-graph submit --text "TSMC cuts capex"
uv run signal-graph normalize \
  --raw-item RAW_ITEM_ID \
  --event-type capex_cut \
  --direction negative \
  --primary-entity TSMC
uv run signal-graph research --event-candidate EVENT_CANDIDATE_ID --bundle-file bundle.json
uv run signal-graph ingest --event-candidate EVENT_CANDIDATE_ID
uv run signal-graph rank --event GRAPH_EVENT_ID
uv run signal-graph explain --event GRAPH_EVENT_ID --candidate SMH
```

Example `bundle.json`:

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

Expected behavior:

- `submit` persists a `RawSourceItem` in SQLite and returns `raw_item_id`
- `normalize` returns `event_candidate_id`
- `research` stores a `ResearchBundle`
- `ingest` returns `graph_event_id`
- `rank` returns JSON candidates with `relationship_path` and `reason_summary`
- `explain` prints a memo and writes a markdown artifact under `.signal-graph/artifacts/`

## Verification Commands

```bash
uv run --group dev python -m pytest -v
uv run ty check
uv run signal-graph doctor
uv run signal-graph version
```

## Repository Responsibilities

- `src/signal_graph/cli/`: command entrypoints
- `src/signal_graph/services/`: pipeline logic
- `src/signal_graph/models/`: canonical objects
- `src/signal_graph/storage/`: SQLite access and schema
- `src/signal_graph/graph/`: graph client and schema helpers
- `tests/`: CLI, service, graph, storage, docs, and end-to-end coverage

## Troubleshooting

- `signal-graph doctor` fails: install missing tooling before debugging repo code.
- Neo4j auth mismatch: either keep the existing password or reset `infra/neo4j/data`.
- `research` says the bundle file is missing: remember that `--bundle-file` is resolved from your current working directory.
- Rank output looks empty or weak: confirm the event has a clear `--primary-entity` and that the local graph has relevant coverage.
- Rank or memo output changed unexpectedly: inspect `.signal-graph/config.toml` and compare it with [`../examples/scoring-policy.example.toml`](../examples/scoring-policy.example.toml).
- Unexpected local state: inspect `.signal-graph/signal_graph.db` and `.signal-graph/artifacts/`.
