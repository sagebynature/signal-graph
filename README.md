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
- Rank likely tickers or ETFs for immediate or short-drift reaction windows
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

### Local Neo4j

- Set `NEO4J_AUTH` before the first `make neo4j-up` if you want a non-default `neo4j/<password>` credential.
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

```bash
uv run signal-graph init
uv run signal-graph submit --text "TSMC cuts capex"
uv run signal-graph normalize \
  --raw-item raw-123 \
  --event-type capex_cut \
  --direction negative \
  --primary-entity TSMC
uv run signal-graph research --event-candidate evt-123 --bundle-file bundle.json
uv run signal-graph ingest --event-candidate evt-123
uv run signal-graph rank --event ge-123
uv run signal-graph explain --event ge-123 --candidate SMH
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

`research` now expects either `--bundle-file` or an explicit `--allow-empty`. Empty placeholder bundles are no longer the default.

## Documentation Map

Start here based on your role:

- Stakeholder or product reader: [`docs/overview/product.md`](docs/overview/product.md)
- Local developer or operator: [`docs/runbooks/operator-guide.md`](docs/runbooks/operator-guide.md)
- Analyst or coding agent user: [`docs/runbooks/analyst-agent-guide.md`](docs/runbooks/analyst-agent-guide.md)
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
- a Neo4j-backed graph ingest path with a seeded semiconductor reference graph
- graph-based ranking that returns path-aware candidate reasons such as direct entity, ETF holdings, and supplier spillover
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
uv run pytest -v
uv run ty check
uv run signal-graph doctor
uv run signal-graph version
```
