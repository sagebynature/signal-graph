# System Overview

## Architecture Summary

`Signal Graph` is organized as a local pipeline with clear separation between command surface, canonical models, local persistence, graph reasoning, and memo artifacts.

At a high level:

`CLI -> services -> models -> SQLite / Neo4j / filesystem artifacts`

## Major Components

### CLI

The CLI in `src/signal_graph/cli/` is the user and agent entrypoint. Each command maps to one stage of the operating workflow.

### Services

The services layer in `src/signal_graph/services/` owns transformation logic:

- raw item creation and persistence
- normalization and dedupe
- research bundle creation
- graph ingest orchestration
- ranking
- explanation and memo writing

### Canonical Models

The models in `src/signal_graph/models/` define the core pipeline objects:

- `RawSourceItem`
- `EventCandidate`
- `ResearchBundle`
- `GraphEvent`
- `RankedCandidate`
- `MemoResponse`

### SQLite Metadata Store

SQLite is the local system of record for the MVP. It stores pipeline objects, provenance-linked records, and local progress across commands.

### Neo4j Runtime

Neo4j is the graph reasoning layer. In the current cut, the graph client and schema are lightweight, but the boundary is in place for richer relationship traversal and constraint management.

### Filesystem Artifacts

The `.signal-graph/` directory stores local database state and memo artifacts. This keeps outputs inspectable and easy for agents to reference.

## Data Flow

### 1. Intake

`submit` or `fetch` produces one or more `RawSourceItem` objects.

### 2. Normalize

`normalize` converts a raw item into an `EventCandidate` and applies basic dedupe behavior using a fingerprint derived from normalized title text.

### 3. Research

`research` creates a `ResearchBundle` for the event candidate. This is where supporting evidence, contradictions, and confidence context belong.

### 4. Ingest

`ingest` validates that the event candidate and research bundle exist, then records a `GraphEvent` and sends the graph payload through the graph client boundary.

### 5. Rank

`rank` returns candidate trade expressions with scores and timing windows.

### 6. Explain

`explain` writes a memo artifact and prints memo text that separates fact, implication, and inference.

## Trust And Provenance Model

The architecture deliberately separates:

- source capture
- normalization
- research and evidence
- graph reasoning
- narrative output

This reduces the risk of explanation layers outrunning the underlying evidence.

## Why SQLite And Neo4j Both Exist

- SQLite is good for local canonical records, deterministic tests, and simple pipeline persistence
- Neo4j is good for explicit relationship paths and propagation reasoning

The system does not force every object into the graph. That is intentional.

## Current Limitations

- public and premium connectors are still stub-level
- graph ingest is currently a thin contract rather than a full relationship engine
- ranking is deterministic and not yet calibrated from real graph output
- explanation is template-driven and not yet evidence-span aware
