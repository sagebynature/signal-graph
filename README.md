# Signal Graph

`Signal Graph` is a CLI-first, provenance-aware trading research toolkit for turning raw market events into explainable trade candidates.

It is built for a workflow where an analyst or coding agent:

1. collects or submits an event,
2. normalizes it into a canonical event candidate,
3. adds supporting research and provenance,
4. ingests the event into a graph reasoning layer,
5. ranks likely trade expressions, and
6. writes a memo that distinguishes fact, graph implication, and inference.

The first cut is intentionally terminal-native. It favors explicit commands, local state, deterministic artifacts, and machine-readable output over a dashboard-first experience.

## What This Repo Is

This repository implements the local operating surface for that workflow:

- a `signal-graph` CLI
- a local SQLite metadata store for pipeline state and provenance
- a Neo4j runtime for graph-oriented reasoning
- filesystem artifacts for cached material and memo output
- runbooks and skill docs for human operators and coding agents

## Intended Users

- Developers and operators who need to run or extend the local toolkit
- Analysts who want a structured workflow for event-driven discretionary research
- Coding agents that need a strict, auditable command order
- Stakeholders who need to understand the product shape, decision model, and architecture

## Core Use Cases

- Capture a breaking event from a manual note, a public source, or a structured feed
- Normalize duplicate or noisy raw inputs into a single event candidate
- Record the evidence used to support or challenge an event hypothesis
- Ingest an event into a relationship graph to reason about spillover paths
- Rank likely equities or ETFs for immediate or short-drift reaction windows
- Produce a memo with explicit provenance boundaries

## Workflow

The canonical pipeline is:

`fetch` or `submit` -> `normalize` -> `research` -> `ingest` -> `rank` -> `explain`

The important operating rule is that `research` is the provenance checkpoint. Downstream ranking or explanation claims should not outrun stored evidence.

## Quick Start

### Bootstrap

```bash
uv sync
uv run signal-graph doctor
uv run signal-graph init
uv run signal-graph version
```

`signal-graph doctor` is non-destructive. It checks runtime readiness for the local workflow, verifies that `.signal-graph/config.toml` is parseable when present, and rejects malformed `NEO4J_AUTH` values. The config file is optional.

### Local Neo4j

- Set `NEO4J_AUTH` before the first `make neo4j-up` if you want a non-default `neo4j/<password>` credential.
- `NEO4J_AUTH` must use the `username/password` format with non-empty values.
- If you change `NEO4J_AUTH` later, remove `./infra/neo4j/data` first or keep using the existing password.
- Removing `./infra/neo4j/data` also deletes your persisted local Neo4j data.
- Authless mode such as `NEO4J_AUTH=none` is not part of this bootstrap setup.

```bash
make neo4j-up
docker compose ps
make neo4j-down
```

Neo4j data, logs, and plugins live under `./infra/neo4j/`.

### Minimal Manual Flow

Create a research bundle first:

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
```

Then run the pipeline with real captured ids:

```bash
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

`research` now expects either `--bundle-file` or an explicit `--allow-empty`. Empty placeholder bundles are no longer the default.

The reference graph load step is explicit. Normal `ingest` no longer seeds demo instruments automatically. Without reference data, rank output will be limited to instruments that already exist in Neo4j.

For a fully isolated, copy-pasteable smoke path that keeps state in a temp directory, use [`docs/runbooks/runnable-smoke-test.md`](docs/runbooks/runnable-smoke-test.md).

### Connector Reality

- `fetch --source web` currently returns a deterministic demo item backed by `example.com`; it is not live public-web retrieval.
- `fetch --source premium` is a placeholder and currently returns no items.
- The seeded demo ranking universe is intentionally small: `TSMC`, `NVDA`, `AMD`, `ASML`, `INTC`, `SMH`, and `SOXX`.

### Customizing Scoring Policy

Scoring policy can be customized locally in `.signal-graph/config.toml`. The file is optional. When present, it must be valid TOML; malformed or unreadable config is not silently ignored. `signal-graph doctor` reports these config problems explicitly, and other commands that load config currently raise an error when they encounter them. The system keeps its built-in defaults, then merges local overrides by exact match:

- path rule match key: `relationship_path`
- event override match key: `event_type + direction + relationship_path`
- event fallback rationale match key: `event_type + direction`

Example:

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

Use the full example file at `docs/examples/scoring-policy.example.toml` as the copyable reference.

## Documentation Map

Start here based on your role:

- Stakeholder or product reader: [`docs/overview/product.md`](docs/overview/product.md)
- Local developer or operator: [`docs/runbooks/operator-guide.md`](docs/runbooks/operator-guide.md)
- Analyst or coding agent user: [`docs/runbooks/analyst-agent-guide.md`](docs/runbooks/analyst-agent-guide.md)
- Runnable onboarding and smoke test: [`docs/runbooks/runnable-smoke-test.md`](docs/runbooks/runnable-smoke-test.md)
- Architecture reader: [`docs/architecture/system-overview.md`](docs/architecture/system-overview.md)

Decision records:

- [`docs/adr/ADR-0001-cli-first-provenance-workflow.md`](docs/adr/ADR-0001-cli-first-provenance-workflow.md)
- [`docs/adr/ADR-0002-sqlite-plus-neo4j-separation.md`](docs/adr/ADR-0002-sqlite-plus-neo4j-separation.md)
- [`docs/adr/ADR-0003-agent-skill-and-command-order.md`](docs/adr/ADR-0003-agent-skill-and-command-order.md)

Legacy plan and design material:

- [`docs/plans/2026-03-19-neo4j-ai-trading-design.md`](docs/plans/2026-03-19-neo4j-ai-trading-design.md)
- [`docs/plans/2026-03-19-neo4j-ai-trading-mvp.md`](docs/plans/2026-03-19-neo4j-ai-trading-mvp.md)

Older planning documents may still refer to `trade-graph`; they describe the same project before the rebrand to `Signal Graph`.

## Current State

The repository currently provides:

- local CLI commands for `doctor`, `init`, `submit`, `fetch`, `normalize`, `research`, `ingest`, `rank`, and `explain`
- a deterministic local test path for the manual event flow
- persisted `fetch` and `submit` intake into SQLite under `.signal-graph/signal_graph.db`
- structured research bundles with stored support URLs, contradictions, evidence spans, and confidence
- a Neo4j-backed graph ingest path with an explicit demo reference-graph seed step
- graph-based ranking that returns only tradable instrument candidates with path-aware reasons such as direct equity exposure, ETF holdings, and supplier spillover
- memo generation that cites stored evidence and separates confirmed fact, graph implication, and assistant inference

This is not yet a production trading system. It is a structured local research toolkit and integration base.

## Non-Goals For This Cut

- automated execution or order routing
- real-time production-grade market data ingestion
- fully calibrated ranking models
- a dashboard or browser UI as the primary interface
- autonomous claims that bypass stored provenance

## Development Verification

```bash
uv run python -m pytest -v
uv run ty check
uv run signal-graph doctor
uv run signal-graph version
```

`uv run ty check` remains a contributor verification step. `signal-graph doctor` does not require `ty` to be installed.
