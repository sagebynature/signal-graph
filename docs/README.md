# Documentation Guide

Use this page to choose the right starting point.

## Start Here

- New reader: go to [`../README.md`](../README.md)
- Product or stakeholder context: go to [`overview/product.md`](overview/product.md)
- Architecture and storage model: go to [`architecture/system-overview.md`](architecture/system-overview.md)
- Local setup and troubleshooting: go to [`runbooks/operator-guide.md`](runbooks/operator-guide.md)
- Research workflow for analysts or agents: go to [`runbooks/analyst-agent-guide.md`](runbooks/analyst-agent-guide.md)
- Reusable prompt templates: go to [`prompts/signal-graph-analyst-prompt-pack.md`](prompts/signal-graph-analyst-prompt-pack.md)

## How The Docs Are Organized

- `README.md` is the landing page. It explains what Signal Graph is, what it is not, and how to run the shortest viable flow.
- `overview/` explains product intent, audience, scope, and maturity.
- `architecture/` explains the pipeline, canonical objects, storage boundaries, and trust model.
- `runbooks/` explains how to operate the repo in practice.
- `prompts/` contains higher-level analyst prompt patterns built on top of the CLI workflow.
- `adr/` contains background design decisions. Treat these as rationale, not onboarding docs.

## Reading Paths

### If you are evaluating the repo

1. Read [`../README.md`](../README.md).
2. Read [`overview/product.md`](overview/product.md).
3. Read [`architecture/system-overview.md`](architecture/system-overview.md).

### If you need to run the repo locally

1. Read [`../README.md`](../README.md).
2. Read [`runbooks/operator-guide.md`](runbooks/operator-guide.md).
3. If you will analyze events, read [`runbooks/analyst-agent-guide.md`](runbooks/analyst-agent-guide.md).

### If you are using Signal Graph for research output

1. Read [`../README.md`](../README.md).
2. Read [`runbooks/analyst-agent-guide.md`](runbooks/analyst-agent-guide.md).
3. Use [`prompts/signal-graph-analyst-prompt-pack.md`](prompts/signal-graph-analyst-prompt-pack.md) when you want reusable prompt wording.

## Background References

- [`adr/ADR-0001-cli-first-provenance-workflow.md`](adr/ADR-0001-cli-first-provenance-workflow.md)
- [`adr/ADR-0002-sqlite-plus-neo4j-separation.md`](adr/ADR-0002-sqlite-plus-neo4j-separation.md)
- [`adr/ADR-0003-agent-skill-and-command-order.md`](adr/ADR-0003-agent-skill-and-command-order.md)
