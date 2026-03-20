# System Overview

## Architecture Summary

`Signal Graph` is a local pipeline with a strict separation between command surface, transformation logic, canonical models, persistence, graph reasoning, and memo output.

At a high level:

`CLI -> services -> models -> SQLite / Neo4j / filesystem artifacts`

That separation matters because the repo is built to make the research chain inspectable instead of collapsing everything into one opaque scoring step.

## Major Components

### CLI

The CLI under `src/signal_graph/cli/` is the operating contract for both humans and coding agents. Each command maps to one stage of the workflow.

### Services

The services layer under `src/signal_graph/services/` owns the domain logic:

- raw item creation and persistence
- normalization and dedupe
- research bundle creation
- graph ingest orchestration
- ranking
- memo generation

### Canonical Models

The models under `src/signal_graph/models/` define the main objects that move through the pipeline:

- `RawSourceItem`
- `EventCandidate`
- `ResearchBundle`
- `GraphEvent`
- `RankedCandidate`
- `MemoResponse`

### SQLite

SQLite under `.signal-graph/signal_graph.db` is the local system of record for this MVP. It stores pipeline objects, provenance-linked data, and local progress across commands.

### Neo4j

Neo4j is the graph reasoning layer. The current implementation is intentionally small, but the boundary already exists for explicit relationship traversal and richer ingest logic.

### Filesystem Artifacts

The `.signal-graph/` directory holds local project state:

- `signal_graph.db` for SQLite state
- `artifacts/` for generated memo output
- `config.toml` for optional local overrides

## Canonical Object Lifecycle

### 1. Intake

`submit` or `fetch` produces one or more `RawSourceItem` records.

### 2. Normalize

`normalize` converts a raw item into an `EventCandidate`. It also applies basic dedupe behavior using a fingerprint derived from the normalized title text.

### 3. Research

`research` creates a `ResearchBundle` for the event candidate. This is where supporting documents, contradictions, evidence spans, confidence, and notes belong.

### 4. Ingest

`ingest` validates that the event candidate and research bundle exist, creates a `GraphEvent`, and sends the graph payload through the Neo4j boundary.

### 5. Rank

`rank` returns candidate instruments with scores, timing windows, matched entities, relationship paths, and short reasons.

### 6. Explain

`explain` writes a memo artifact and prints memo text that separates confirmed facts, graph implications, and analyst inference.

## Why SQLite And Neo4j Both Exist

SQLite and Neo4j do different jobs.

- SQLite is better for canonical local records, deterministic tests, and simple state lookup across the whole pipeline.
- Neo4j is better for explicit relationship paths and spillover reasoning.

The system does not force every object into the graph. That is intentional.

## Trust And Provenance Model

The architecture deliberately separates:

- source capture
- normalization
- research and evidence
- graph reasoning
- narrative output

That separation makes it easier to see when a conclusion is supported, when it is inferred, and where the chain breaks if the result is weak.

## Current Limitations

- Connectors are still lightweight. `web` returns stub public-web results and `premium` is currently a placeholder.
- Graph ingest is a thin contract, not a full production graph ingestion engine.
- Ranking is deterministic and not calibrated from live market outcomes.
- Memo generation is template-driven and not yet deeply evidence-span aware.

## Read Next

- Landing page: [`../../README.md`](../../README.md)
- Product context: [`../overview/product.md`](../overview/product.md)
- Local setup: [`../runbooks/operator-guide.md`](../runbooks/operator-guide.md)
- Workflow usage: [`../runbooks/analyst-agent-guide.md`](../runbooks/analyst-agent-guide.md)
