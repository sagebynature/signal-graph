# ADR-0006: Require MCP Transport Parity Between Stdio And HTTP

## Status

Accepted

## Context

Signal Graph already exposes an stdio MCP surface. V2 needs the same memory operations to work through both stdio and HTTP so local tools, remote trusted hosts, and evaluation harnesses do not drift into different capability sets.

## Decision Drivers

- one capability surface for capture, retrieval, explanation, and correction
- one schema and error model across transports
- simpler testability and host integration guidance
- less product ambiguity for tool builders

## Considered Options

### Option 1: Keep Stdio As The Only MCP Transport

- Pros: simpler implementation and security posture
- Cons: blocks trusted-environment HTTP hosts and parity evals

### Option 2: Let HTTP Diverge From Stdio Over Time

- Pros: faster transport-specific iteration
- Cons: fragmented docs, fragmented tests, and inconsistent client expectations

### Option 3: Share One Service Layer With Transport Adapters

- Pros: parity by construction, cleaner tests, and clearer product boundaries
- Cons: adapter discipline is required whenever the API evolves

## Decision

Expose the same core memory capabilities over stdio and HTTP by routing both transports through shared service-layer handlers, shared schemas, and a shared core error model.

## Consequences

### Positive

- parity can be verified with one test matrix
- host examples and docs stay coherent
- transport differences remain infrastructural rather than semantic

### Negative

- transport-specific shortcuts become less acceptable
- parity regressions must block release

## Related Documents

- `docs/architecture/system-overview.md`
- `.omx/plans/test-spec-signal-graph-v2-memory-rewrite.md`
