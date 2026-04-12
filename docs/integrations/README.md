# MCP Host Validation And Integration Examples

This directory tracks evidence-backed MCP host compatibility for Signal Graph.

## Validation policy

- `validated` means we have a committed evidence artifact showing the host config shape, validation date, proof path, and observed result.
- `example-only` means the config example is provided from current docs/runtime knowledge, but we did not complete a full host validation pass.
- `deferred` means we intentionally have not validated the host yet.

## Canonical files

- `mcp-host-matrix.json` — machine-readable support matrix
- `evidence/` — per-host evidence artifacts
- `docs/examples/mcp/` — copy-pasteable config examples

## Current first-wave scope

- validated: **Claude Code**, **Codex CLI**
- example-only: **Cursor**
- deferred: **Claude Desktop** until a supported validation environment is available

## Runtime contract dependency

All host examples and validation claims must wrap the same Signal Graph runtime contract:

- `signal-graph-mcp`
- `signal-graph mcp-server`
- `signal-graph bootstrap-describe`

If those entrypoints change, this directory must be updated in the same change set.
