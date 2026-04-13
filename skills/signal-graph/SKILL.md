---
name: signal-graph
description: Operate the local Signal Graph memory and decision-support toolkit through its supported CLI and MCP surfaces.
---

# Signal Graph

Use Signal Graph as a local, provenance-aware memory system for capture, journaling, recall, and MCP-backed host integrations.

## Working Model

Supported workflow:

1. verify prerequisites with `doctor`
2. initialize local state with `init`
3. inspect runtime contracts with `bootstrap-describe` and `automation-describe`
4. capture a signal with `capture-signal`
5. journal it with `journalize-signal`
6. recall prior work with `recall-signal`
7. start the MCP server with `mcp-server` or `signal-graph-mcp` when host integration is needed

Signal Graph is local-first. It stores journal signals and recall artifacts in SQLite, projects journaled signals into a graph path, and keeps runtime guidance explicit through CLI contracts.

## Command Contract

- `signal-graph doctor` — validate prerequisites and config
- `signal-graph init` — prepare local project directories and SQLite state
- `signal-graph bootstrap-describe --format {json|markdown}` — inspect the supported bootstrap contract
- `signal-graph automation-describe --format {json|markdown}` — inspect host automation guidance
- `signal-graph capture-signal ...` — persist a provenance-rich signal
- `signal-graph journalize-signal --signal SIGNAL_ID` — attach a graph path to a captured signal
- `signal-graph recall-signal --query ...` — generate structured recall output and a markdown artifact
- `signal-graph integration-install --host ...` / `integration-audit` / `integration-uninstall` — manage supported host setups
- `signal-graph mcp-server` / `signal-graph-mcp` — start the stdio MCP server

## Operating Defaults

- Prefer `bootstrap-describe` before hand-writing runtime instructions.
- Prefer `automation-describe` before changing integration docs or host config.
- Prefer already captured local signals before creating duplicate entries.
- Treat recall output as decision-support evidence, not autonomous judgment.
- When Neo4j is unavailable, stop and report the environment gap before continuing with graph journaling.

## Read More Only When Needed

Read `../../docs/README.md` for the full documentation map.
Read `../../docs/runbooks/operator-guide.md` when debugging environment, Neo4j, or local config issues.
Read `../../docs/architecture/system-overview.md` when reasoning about SQLite, graph journaling, and MCP boundaries.
