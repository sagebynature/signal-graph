# Documentation Guide

Use this page to choose the right starting point for the **V2 memory and decision-support rewrite**.

## Start Here

- New reader: go to [`../README.md`](../README.md)
- Agent/operator bootstrap contract: run `uv run signal-graph bootstrap-describe`
- Product or stakeholder context: go to [`overview/product.md`](overview/product.md)
- Architecture and storage model: go to [`architecture/system-overview.md`](architecture/system-overview.md)
- Local setup and troubleshooting: go to [`runbooks/operator-guide.md`](runbooks/operator-guide.md)
- Brownfield research workflow for analysts or agents: go to [`runbooks/analyst-agent-guide.md`](runbooks/analyst-agent-guide.md)
- MCP host validation and examples: go to [`integrations/README.md`](integrations/README.md)
- Operational automation for validated hosts: see runtime command `signal-graph automation-describe`
- Reusable prompt templates: go to [`prompts/signal-graph-analyst-prompt-pack.md`](prompts/signal-graph-analyst-prompt-pack.md)

## How The Docs Are Organized

- `README.md` is the landing page. It frames Signal Graph as the V2 memory-system rewrite while honestly calling out the still-operational V1 runtime.
- `overview/` explains product intent, audience, scope, and the shift to owner-scoped memory + decision support.
- `architecture/` explains the target domain model, storage split, transport boundaries, and provenance rules.
- `runbooks/` explains how to operate the current repo in practice while the rewrite is in flight.
- `prompts/` contains higher-level analyst prompt patterns built on top of the brownfield CLI workflow.
- `adr/` contains background design decisions. Treat these as rationale, not onboarding docs.

## Reading Paths

### If you are evaluating the V2 rewrite

1. Read [`../README.md`](../README.md).
2. Read [`overview/product.md`](overview/product.md).
3. Read [`architecture/system-overview.md`](architecture/system-overview.md).
4. Review ADRs `0004` through `0008` for the accepted rewrite decisions.

### If you need to run the repo locally today

1. Read [`../README.md`](../README.md).
2. Read [`runbooks/operator-guide.md`](runbooks/operator-guide.md).
3. If you will use the brownfield event/research workflow, read [`runbooks/analyst-agent-guide.md`](runbooks/analyst-agent-guide.md).

### If you are validating memory capture, explanation, or corrections

1. Read [`../README.md`](../README.md).
2. Read [`architecture/system-overview.md`](architecture/system-overview.md).
3. Review the V2 ADRs in [`adr/`](adr/).
4. Use [`integrations/README.md`](integrations/README.md) for MCP host surfaces and examples.

## Background References

- [`adr/ADR-0001-cli-first-provenance-workflow.md`](adr/ADR-0001-cli-first-provenance-workflow.md)
- [`adr/ADR-0002-sqlite-plus-neo4j-separation.md`](adr/ADR-0002-sqlite-plus-neo4j-separation.md)
- [`adr/ADR-0003-agent-skill-and-command-order.md`](adr/ADR-0003-agent-skill-and-command-order.md)
- [`adr/ADR-0004-v2-memory-ontology.md`](adr/ADR-0004-v2-memory-ontology.md)
- [`adr/ADR-0005-v2-storage-of-record-split.md`](adr/ADR-0005-v2-storage-of-record-split.md)
- [`adr/ADR-0006-v2-mcp-transport-parity.md`](adr/ADR-0006-v2-mcp-transport-parity.md)
- [`adr/ADR-0007-v2-hook-ingestion-envelope.md`](adr/ADR-0007-v2-hook-ingestion-envelope.md)
- [`adr/ADR-0008-v2-http-trusted-environment-boundary.md`](adr/ADR-0008-v2-http-trusted-environment-boundary.md)
