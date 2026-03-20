# Signal Graph

`Signal Graph` is a local, CLI-first trading research toolkit for turning a market event into an explainable trade hypothesis with explicit provenance.

It is not an execution engine. It is a structured workflow for moving from a raw event to a memo that separates confirmed fact, graph implication, and analyst inference.

## What You Get

- A `signal-graph` CLI with explicit, auditable stages
- A local SQLite store for pipeline state and provenance
- A Neo4j runtime for graph-oriented reasoning
- Markdown memo artifacts under `.signal-graph/artifacts/`
- Role-based docs for operators, analysts, stakeholders, and coding agents

## The Core Workflow

Run the pipeline in this order:

`fetch` or `submit` -> `normalize` -> `research` -> `ingest` -> `rank` -> `explain`

The important rule is simple: do not skip `research`. It is the provenance checkpoint for everything downstream.

## Who This Repo Is For

- Operators and developers who need to run or extend the local toolkit
- Analysts who want a disciplined event-to-thesis workflow
- Coding agents that need explicit command order and inspectable local state
- Stakeholders who need to understand the product shape and architecture

## Quick Start

### 1. Install Prerequisites

You need:

- Python 3.12
- `uv`
- `ty`
- Docker
- `make`

### 2. Bootstrap The Local Environment

```bash
uv sync --group dev
uv run signal-graph doctor
uv run signal-graph init
uv run signal-graph version
```

`signal-graph doctor` reports whether `docker`, `uv`, and `ty` are available. It also reports whether `.signal-graph/config.toml` exists. `config: missing` is normal until you create a local config file.

### 3. Start Neo4j

Before first startup, set `NEO4J_AUTH` if you do not want the default `neo4j/password` credential.

```bash
make neo4j-up
docker compose ps
```

Operational notes:

- Neo4j data, logs, and plugins live under `infra/neo4j/`.
- Wait for the container to become `healthy` before using `ingest`, `rank`, or `explain`.
- If you change `NEO4J_AUTH`, you may need to clear `infra/neo4j/data` or keep using the old password.
- Removing `infra/neo4j/data` also removes local Neo4j state.

### 4. Run A Minimal Manual Flow

The commands below use placeholder IDs. Replace each ID with the value returned by the previous command.

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

`research` requires either `--bundle-file` or `--allow-empty`. Relative bundle paths are resolved from your current working directory.

### 5. Inspect Local State

After `init` and a successful workflow run, the important local paths are:

- `.signal-graph/signal_graph.db`: SQLite system of record for the local pipeline
- `.signal-graph/artifacts/`: generated memo artifacts
- `.signal-graph/config.toml`: optional local config overrides

## Local Configuration

You can override ranking and memo behavior in `.signal-graph/config.toml` under `[scoring_policy]`.

The system merges:

1. Built-in defaults
2. Path overrides matched by `relationship_path`
3. Event overrides matched by `event_type + direction + relationship_path`

Reference example:

- [`docs/examples/scoring-policy.example.toml`](docs/examples/scoring-policy.example.toml)

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

Malformed scoring policy config fails fast instead of being ignored.

## Documentation Map

Start with [`docs/README.md`](docs/README.md) for the full documentation guide.

- Product context: [`docs/overview/product.md`](docs/overview/product.md)
- Architecture and storage model: [`docs/architecture/system-overview.md`](docs/architecture/system-overview.md)
- Setup, runtime, and troubleshooting: [`docs/runbooks/operator-guide.md`](docs/runbooks/operator-guide.md)
- Research workflow for analysts and agents: [`docs/runbooks/analyst-agent-guide.md`](docs/runbooks/analyst-agent-guide.md)
- Reusable prompt templates: [`docs/prompts/signal-graph-analyst-prompt-pack.md`](docs/prompts/signal-graph-analyst-prompt-pack.md)
- Background design decisions: `docs/adr/`

## Current State

This repository is an MVP. It already supports:

- The full local CLI command chain from intake through memo output
- Stored raw items, event candidates, research bundles, and graph events
- Graph-backed ranking with relationship-path explanations
- Markdown memo artifacts with provenance-aware wording
- Local scoring-policy overrides
- Test coverage for the manual CLI flow

What it does not try to be in this cut:

- An order execution or brokerage integration layer
- A production market-data system
- A calibrated trading model
- A dashboard-first product
- A system that skips stored evidence and still claims confidence

## Development Verification

```bash
uv run --group dev python -m pytest -v
uv run ty check
uv run signal-graph doctor
uv run signal-graph version
```
