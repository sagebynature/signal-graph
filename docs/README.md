# Documentation Guide

Signal Graph is documented as a **current memory and decision-support system** with a small, supported command surface.

## Start Here

- Read `../README.md` for the product overview and quick start.
- Read `runbooks/operator-guide.md` for runtime setup, smoke steps, automation, and troubleshooting.
- Read `integrations/README.md` for MCP host examples and validation status.

## Documentation Map

- `overview/product.md` — what Signal Graph is for, who it serves, and what it does not try to do
- `architecture/system-overview.md` — CLI, storage, graph, and MCP boundaries
- `runbooks/operator-guide.md` — supported local operator workflow
- `integrations/README.md` — validated MCP host matrix and example configs
- `adr/` — accepted architecture decisions

## Reading Paths

### If you are evaluating the product
Read `overview/product.md`, then `architecture/system-overview.md`.

### If you need to run the repo locally today
Read `runbooks/operator-guide.md`, then `integrations/README.md`.

### If you are validating memory capture, recall, explanation, or correction behavior
Read `architecture/system-overview.md`, `runbooks/operator-guide.md`, and the accepted ADRs referenced there.

## Runtime Contracts

Supported runtime discovery commands:

- `signal-graph bootstrap-describe`
- `signal-graph automation-describe`
- `signal-graph integration-audit`
- `signal-graph mcp-server`
- `signal-graph-mcp`
