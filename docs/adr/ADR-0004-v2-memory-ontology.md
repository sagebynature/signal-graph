# ADR-0004: Define The V2 Memory Ontology

## Status

Accepted

## Context

The V1 event-to-thesis objects are too narrow for the rewrite. Signal Graph V2 needs to represent humans, AI actors, shared artifacts, later explanations, and corrective feedback without collapsing them into one generic event record.

## Decision Drivers

- explicit owner linkage for every AI action
- durable provenance across tools, devices, and sessions
- first-class support for shared artifacts and later corrections
- deterministic explanation responses with optional confidence-labeled `why`

## Considered Options

### Option 1: Extend The V1 Trading/Event Objects

- Pros: less near-term naming churn
- Cons: wrong center of gravity, awkward fit for owners, shares, and corrections

### Option 2: Store A Flat Transcript/Event Log Only

- Pros: simple ingest story
- Cons: too weak for explanation, artifact recall, or correction semantics

### Option 3: Adopt An Explicit Memory Ontology

- Pros: clear contracts for ownership, provenance, explanation, and revision
- Cons: requires more up-front modeling discipline

## Decision

Adopt a canonical V2 ontology centered on:

- `Owner`
- `Actor`
- `SessionContext`
- `ActionEvent`
- `Artifact`
- `ShareEvent`
- `DerivedInterpretation`
- `CorrectionRedaction`
- optional confidence-labeled `WhyInference`

Every AI actor action must link to a human owner. `WhyInference` remains optional and must never be stored as an observed fact.

## Consequences

### Positive

- explanation shapes can stay deterministic
- shared documents and later corrections become first-class records
- owner/actor provenance can be enforced as an invariant

### Negative

- migration from V1 names requires explicit boundary work
- more record types means more documentation and test coverage

## Related Documents

- `docs/overview/product.md`
- `docs/architecture/system-overview.md`
- `.omx/plans/prd-signal-graph-v2-memory-rewrite.md`
