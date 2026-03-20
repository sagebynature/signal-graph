# ADR-0001: Adopt A CLI-First, Provenance-Aware Workflow

## Status

Accepted

## Context

The project needed an initial product surface for event-driven trading research. The main candidates were:

- a dashboard-first application
- a library-first internal toolkit
- a CLI-first workflow that can be used by both humans and coding agents

The target operator for the MVP is a terminal-native analyst or agent. The workflow also needs explicit provenance boundaries so downstream scoring and memo generation do not outrun the evidence.

## Decision Drivers

- deterministic operation for humans and agents
- explicit command sequencing
- low setup friction for local development
- auditability of intermediate artifacts
- ability to delay UI decisions until the workflow stabilizes

## Considered Options

### Option 1: Dashboard-First Product

- Pros: easier to demo visually, more approachable for non-technical users
- Cons: higher implementation overhead, weaker fit for coding agents, more implicit state transitions

### Option 2: Library-First Toolkit

- Pros: flexible for developers, minimal surface area
- Cons: weak operational contract, too much assumed context for analysts and agents

### Option 3: CLI-First Workflow

- Pros: explicit, scriptable, agent-friendly, easy to verify locally
- Cons: less polished for non-technical stakeholders, requires stronger documentation

## Decision

Adopt a CLI-first, provenance-aware workflow as the primary product surface for the MVP.

## Consequences

### Positive

- commands provide a stable operating contract
- local artifacts are easy to inspect and test
- coding agents can follow a strict workflow without hidden UI state
- provenance rules can be enforced at command boundaries

### Negative

- the product is less immediately demo-friendly than a polished UI
- documentation quality becomes critical
- some future users may still need a higher-level interface

## Related Documents

- `docs/overview/product.md`
- `docs/architecture/system-overview.md`
