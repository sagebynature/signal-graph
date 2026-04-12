# ADR-0005: Split V2 Storage Of Record Between Raw Artifacts, Append-Only Events, And Derived Projections

## Status

Accepted

## Context

Signal Graph V2 must preserve raw source truth while still supporting revisable summaries, graph traversals, markdown views, and explanation queries. Storing everything in one mutable layer would blur source truth and derived interpretation.

## Decision Drivers

- immutable preservation of raw artifacts
- append-only capture history for actions and shares
- revisable derived interpretations without rewriting source records
- explicit graph/query projection boundaries

## Considered Options

### Option 1: Graph As The Only Source Of Truth

- Pros: one query surface
- Cons: poor fit for raw blobs, append-only evidence, and revision-safe derived layers

### Option 2: Relational Store As The Only Source Of Truth

- Pros: simple local indexing and testing
- Cons: weaker fit for relationship traversal and explanation assembly

### Option 3: Split The System Of Record By Responsibility

- Pros: raw artifact truth, append-only event history, and query projections can evolve independently
- Cons: more boundary design and synchronization work

## Decision

Use a responsibility split:

- canonical raw artifacts are preserved on disk
- append-only event envelopes are durably indexed as the capture history
- graph/query projections support relationship traversal and explanation assembly
- markdown views and summaries are derived projections, not source truth

Corrections update derived layers and policy-aware query behavior; they do not mutate the original raw artifact or captured event payload.

## Consequences

### Positive

- raw artifacts remain auditable
- derived summaries/topics can be corrected safely
- storage boundaries stay testable and easier to reason about

### Negative

- operators and developers must understand multiple persistence roles
- projection freshness and replay behavior need explicit coverage

## Related Documents

- `docs/architecture/system-overview.md`
- `.omx/plans/prd-signal-graph-v2-memory-rewrite.md`
