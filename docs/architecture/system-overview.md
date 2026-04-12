# System Overview

## Architecture Summary

`Signal Graph` V2 is a local memory and decision-support architecture with a strict separation between capture surfaces, canonical domain records, storage-of-record boundaries, derived projections, and retrieval/explanation transports.

At a high level:

`CLI + MCP transports -> capture/command services -> canonical memory domain -> filesystem/SQLite/graph projections -> retrieval/explanation/correction responses`

The rewrite keeps the repository's CLI-first operating style, but the target architecture is no longer an event-to-trade pipeline. It is an owner-scoped memory system that can later explain prior actions and incorporate corrections without mutating raw truth.

## Major Components

### Capture Surfaces

The CLI under `src/signal_graph/cli/` and the MCP server entrypoints remain the operating contract for both humans and coding agents. V2 requires the same core memory capabilities to be reachable through stdio and HTTP transports.

### Canonical Memory Domain

The V2 domain distinguishes these first-class records:

- `Owner`
- `Actor`
- `SessionContext`
- `ActionEvent`
- `Artifact`
- `ShareEvent`
- `DerivedInterpretation`
- `CorrectionRedaction`
- optional confidence-labeled `WhyInference`

Every AI actor action must link to a human owner.

### Append-Only Event And Artifact Storage

Raw hook payloads, share events, and source artifacts are preserved canonically. The system of record is append-only for captured events and immutable for raw artifact payloads. Later summaries, topics, or interpretations are stored as separate derived layers.

### Projection And Query Layers

Structured indexes, markdown views, and graph-oriented projections exist to make memory queryable by who, topic, and date. These projections are allowed to change when corrections arrive; the raw event and artifact record is not.

### Explanation And Correction Services

Retrieval and explanation services assemble deterministic response shapes that include owner, actor, queried action/decision, provenance chain, supporting evidence refs, and confidence-labeled `why` when present. Correction/redaction services persist downstream policy changes and make those effects visible on subsequent reads.

### Brownfield V1 Runtime

The existing event/research/rank/memo code remains in the repository as a brownfield reference lane. It is no longer the target product architecture for V2, but it still informs migration constraints and local operational compatibility.

## Storage-Of-Record Split

The favored V2 storage boundary is:

- canonical raw artifacts on disk
- append-only event envelopes with durable local indexing
- graph/query projections for relationship traversal and explanation assembly
- derived markdown or summary views generated from canonical records

This keeps raw source material and append-only capture history stable while allowing query/index layers to evolve.

## MCP Transport Model

Both transports must wrap the same service-layer behavior.

- **stdio** remains the default local/agent integration surface
- **HTTP** is an MVP convenience transport for trusted environments only
- schema shape, capability surface, and core error model must remain transport-parity compatible

## Trust And Provenance Model

The architecture deliberately separates:

- owner identity
- actor identity
- capture of facts/actions/artifacts
- derived interpretation
- confidence-labeled inference
- correction/redaction policy

That separation makes it easier to show what is observed, what is inferred, what changed later, and what should no longer be repeated.

## Current Implementation Notes

Today the repo still contains V1-oriented models, services, SQLite state, Neo4j graph logic, and memo artifacts. Those components are brownfield inputs to the rewrite, not the final V2 architecture contract.

## Read Next

- Landing page: [`../../README.md`](../../README.md)
- Product context: [`../overview/product.md`](../overview/product.md)
- Local setup: [`../runbooks/operator-guide.md`](../runbooks/operator-guide.md)
- Brownfield workflow usage: [`../runbooks/analyst-agent-guide.md`](../runbooks/analyst-agent-guide.md)
