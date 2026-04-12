# Claude Desktop MCP Validation — Deferred on 2026-04-12

- Host: Claude Desktop
- Status: deferred
- Config example: `docs/examples/mcp/claude-desktop.json`
- Source reference: local `claude mcp add-from-claude-desktop --help`

## Why deferred

This Linux environment cannot complete the native Claude Desktop import/host flow. Running the available import helper reports:

> Unsupported platform - Claude Desktop integration only works on macOS and WSL.

## Next validation requirement

Promote Claude Desktop beyond `deferred` only after validating on macOS or WSL with:

1. config acceptance in the real host,
2. MCP startup proof,
3. `tools/list` visibility,
4. one named Signal Graph tool call or a documented host limitation,
5. a dated evidence artifact.
