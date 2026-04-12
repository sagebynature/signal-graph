# ADR-0007: Normalize Hook Capture Into A V2 Event Envelope

## Status

Accepted

## Context

The rewrite must ingest activity from multiple AI tools, including pre-action and post-output hooks. Raw host payloads differ, but explanation and correction logic need a stable capture contract.

## Decision Drivers

- host-agnostic ingest across Claude Code, OpenCode, Gemini, and Codex
- explicit owner, actor, and session linkage
- append-only event history with payload references
- separation between observed actions and inferred meaning

## Considered Options

### Option 1: Keep Host-Specific Payloads As The Main Contract

- Pros: minimal transformation logic
- Cons: every downstream consumer becomes host-aware and brittle

### Option 2: Capture Only Post-Processed Summaries

- Pros: smaller payloads
- Cons: loses provenance, phase detail, and replay value

### Option 3: Normalize To A Canonical Event Envelope

- Pros: stable downstream contracts, replayable ingest, and easier parity testing
- Cons: envelope design must be maintained as hosts evolve

## Decision

Normalize hook capture into an append-only event envelope that includes, at minimum:

- owner identity reference
- actor identity reference
- session/context reference
- host/runtime metadata
- action phase such as pre-action or post-output
- timestamps
- payload/artifact references
- provenance and capture-policy metadata

Derived interpretations remain separate records layered on top of the observed envelope.

## Consequences

### Positive

- downstream explanation and correction logic can stay host-agnostic
- new hosts can be added behind one canonical ingest boundary
- replay/invariant tests become more realistic

### Negative

- adapters must keep up with upstream host payload changes
- envelope versioning becomes part of the compatibility contract

## Related Documents

- `docs/architecture/system-overview.md`
- `.omx/plans/prd-signal-graph-v2-memory-rewrite.md`
