# ADR-0002: Separate Local Metadata Storage From Graph Reasoning

## Status

Accepted

## Context

The system needs to persist canonical pipeline state, provenance artifacts, and graph-oriented relationship reasoning. A single storage technology could have been forced to handle both roles, but the responsibilities are materially different.

## Decision Drivers

- simple local persistence for CLI workflows
- inspectable and deterministic test behavior
- explicit graph traversal for spillover reasoning
- minimal operational complexity in the MVP

## Considered Options

### Option 1: Neo4j For Everything

- Pros: one data platform, unified query model
- Cons: awkward fit for pipeline bookkeeping, heavier local testing burden, over-graphing canonical records

### Option 2: SQLite For Everything

- Pros: simple local setup, deterministic tests, minimal operational complexity
- Cons: weaker fit for explicit relationship traversal and graph explainability

### Option 3: SQLite For Metadata, Neo4j For Reasoning

- Pros: each store handles its natural role, local persistence stays simple, graph reasoning remains explicit
- Cons: dual-storage architecture adds boundary design work

## Decision

Use SQLite as the MVP system of record for canonical pipeline state and provenance, and use Neo4j as the graph reasoning layer.

## Consequences

### Positive

- local state stays simple and testable
- graph logic can evolve independently
- not every object must be shaped as a graph node prematurely

### Negative

- ingest boundaries must be explicit and maintained carefully
- eventual consistency concerns appear once graph logic becomes richer
- operators need to understand two storage roles instead of one

## Related Documents

- `docs/architecture/system-overview.md`
- `src/signal_graph/storage/schema.sql`
- `src/signal_graph/graph/schema.py`
