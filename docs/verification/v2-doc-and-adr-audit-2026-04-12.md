# V2 Documentation And ADR Audit — 2026-04-12

## Scope

This audit checks the V2 rewrite documentation lane against the approved PRD and test spec.

## Verified V2 Primary Docs

- `README.md` now frames Signal Graph as a local-first, cross-tool decision-memory rewrite.
- `docs/README.md` now routes readers through V2 docs first and archives V1 references.
- `docs/overview/product.md` describes the V2 owner / actor / artifact / correction product shape.
- `docs/architecture/system-overview.md` documents the V2 ontology, storage contract, transport contract, and brownfield status.
- `docs/runbooks/operator-guide.md` documents runtime bootstrap, integration automation, stdio entrypoints, and trusted-environment HTTP posture.
- `docs/integrations/README.md` documents validated hosts, example-only hosts, deferred hosts, and current runtime entrypoints.
- `docs/overview/v1-supersession.md` provides the required V1 supersession and archive pointer.

## ADR Inventory

### Current V2 ADRs

- `ADR-0004` — V2 memory ontology
- `ADR-0005` — storage-of-record split between raw artifacts, append-only events, and derived projections
- `ADR-0006` — MCP transport parity between stdio and HTTP
- `ADR-0007` — hook ingestion event envelope
- `ADR-0008` — trusted-environment HTTP boundary for the MVP

### Legacy ADR posture

- `ADR-0001` through `ADR-0003` remain brownfield context for the V1-oriented runtime and operator workflow.
- `ADR-0004` through `ADR-0008` define the accepted V2 rewrite direction.

## Acceptance-Criteria Coverage

- **Docs/value-prop rewrite:** covered by the rewritten root docs, product overview, and system overview.
- **ADR set complete:** covered by `ADR-0004` through `ADR-0007` plus explicit legacy supersession notes.
- **V1 supersession cleanup:** covered by `docs/overview/v1-supersession.md` and legacy runbook repositioning.
- **Trusted HTTP boundary:** called out in README, system overview, operator guide, and integrations guide.

## Remaining Brownfield Reality

The codebase still contains V1 implementation surfaces (`journal`, legacy MCP server, event/research/rank/explain flow). Docs now describe them as brownfield references instead of target architecture.

## Recommended Follow-through

- Keep future implementation PRs aligned with the V2 terminology introduced here.
- Add transport parity and hook-adapter evidence artifacts as those lanes land.
- Do not restore V1 trading-research framing in top-level docs.
