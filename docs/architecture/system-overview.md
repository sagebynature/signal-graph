# System Overview

## Architecture Summary

Signal Graph is a local memory and decision-support architecture with a strict separation between capture surfaces, persisted journal state, graph journaling, recall artifacts, and MCP transport.

At a high level:

`CLI + MCP transports -> capture/journal services -> local SQLite state + graph path projection -> recall/explanation artifacts`

## Major Components

### Capture surfaces
The supported CLI captures and inspects signals through:

- `capture-signal`
- `journalize-signal`
- `recall-signal`
- `bootstrap-describe`
- `automation-describe`

### Local storage of record
SQLite stores:

- `journal_signals`
- `recall_artifacts`

These records are the local source of truth for capture and recall flows.

### Graph journaling layer
Journaled signals are projected into Neo4j-backed paths so later explanation and recall output can show where a signal belongs in context.

### Recall and artifact layer
Recall queries return structured matches plus a markdown artifact that records the query contract, graph paths, and provenance contract.

### MCP transport model
Signal Graph exposes a published stdio MCP entrypoint (`signal-graph-mcp`) and an equivalent CLI launch path (`signal-graph mcp-server`). Host validation examples live in `docs/integrations/`.

## Trust And Provenance Model

The system deliberately separates:

- signal origin
- source metadata
- agent or session identity
- raw text/payload
- graph path projection
- recall artifact output

That separation makes it easier to distinguish observed facts from later interpretation.

## Current Implementation Notes

- `signal-graph init` prepares the local project directories and SQLite state.
- `capture-signal`, `journalize-signal`, and `recall-signal` are the primary supported workflow commands.
- bootstrap and automation guidance must stay aligned with CLI help and MCP behavior.
- local Neo4j availability still matters for graph journaling and MCP-backed recall workflows.

## Read Next

- `../overview/product.md`
- `../runbooks/operator-guide.md`
- `../integrations/README.md`
