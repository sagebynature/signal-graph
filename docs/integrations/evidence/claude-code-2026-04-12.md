# Claude Code MCP Validation — 2026-04-12

- Host: Claude Code
- Status: validated
- Source doc: https://code.claude.com/docs/en/mcp
- Transport: stdio

## Config shape used

See `docs/examples/mcp/claude-code-local.json`.

## Validation evidence

1. `claude mcp add-json -s local signal-graph '<json>'` accepted the Signal Graph config shape.
2. `claude mcp list` and `claude mcp get signal-graph` showed the configured stdio server and health-check outcome.
3. Signal Graph stdio protocol smoke passes locally via framed `initialize`, `tools/list`, and `tools/call` behavior (`tests/mcp/test_stdio_transport.py`).
4. Signal Graph bootstrap contract and MCP server entrypoints remain aligned with the host example.

## Known caveats / limitations

- Validation is currently bounded to local CLI/config evidence and protocol smoke, not a broad matrix of Claude Code runtime environments.
- Claude Code host validation does not yet include a fully scripted end-to-end tool call through the host itself; the named-tool proof currently comes from the same stdio runtime exercised directly in protocol smoke tests.
