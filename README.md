# Signal Graph

`Signal Graph` is a local, CLI-first **memory and decision-support system** for humans and AI tools.

It captures provenance-rich signals, journals them into a graph-backed path, recalls prior activity with deterministic artifacts, and exposes the same runtime through CLI and MCP surfaces.

## Supported Command Surface

Primary user-facing commands:

- `signal-graph doctor`
- `signal-graph init`
- `signal-graph bootstrap-describe`
- `signal-graph automation-describe`
- `signal-graph capture-signal`
- `signal-graph journalize-signal`
- `signal-graph recall-signal`
- `signal-graph integration-install`
- `signal-graph integration-audit`
- `signal-graph integration-uninstall`
- `signal-graph mcp-server`
- `signal-graph-mcp`

## What Signal Graph Does

- capture owner- and actor-scoped signals with explicit provenance
- preserve raw evidence and artifact references locally
- journal signals into a graph-backed path for later explanation
- recall prior work by query, session, source, or runtime
- expose the same system through a local MCP transport for tool integrations

## Quick Start

### 1. Verify prerequisites

```bash
uv run signal-graph doctor --json
```

### 2. Initialize local state

```bash
uv run signal-graph init
```

This creates `.signal-graph/cache/`, `.signal-graph/artifacts/`, and `.signal-graph/signal_graph.db`.

### 3. Inspect the bootstrap contract

```bash
uv run signal-graph bootstrap-describe --format markdown
```

The bootstrap contract is the canonical runtime guide for supported entrypoints, smoke steps, and MCP expectations.

### 4. Capture, journal, and recall a signal

```bash
uv run signal-graph capture-signal           --text "Agent completed the release checklist signal."           --origin-type agent_artifact           --source-name codex           --process codex           --runtime-family codex           --session-id session-a           --intent-status explicit           --why "Safely finish the release."           --what release           --where notes/release.md

uv run signal-graph journalize-signal --signal SIGNAL_ID
uv run signal-graph recall-signal --query release
```

### 5. Inspect automation and host integration guidance

```bash
uv run signal-graph automation-describe --format markdown
uv run signal-graph integration-install --host claude-code
uv run signal-graph integration-audit --host claude-code --json
```

## MCP Runtime

`Signal Graph` ships a published stdio MCP entrypoint and an equivalent CLI launch path:

- `signal-graph-mcp`
- `signal-graph mcp-server`

Host integration examples and validation evidence live under `docs/integrations/`.

## Documentation Map

- `docs/README.md` — documentation guide and reading paths
- `docs/runbooks/operator-guide.md` — runtime, bootstrap, automation, and troubleshooting guidance
- `docs/overview/product.md` — product framing and supported use cases
- `docs/architecture/system-overview.md` — architecture boundaries and storage/transport model
- `docs/integrations/README.md` — MCP host matrix and installation examples

## Current Scope

Signal Graph is intentionally local-first. It favors explicit commands, deterministic artifacts, and inspectable provenance over hidden automation or a dashboard-first UI.

Non-goals for this cut:

- opaque autonomous decision-making
- public multi-tenant hosting
- mutating raw truth when later corrections arrive
- unsupported legacy workflow compatibility
