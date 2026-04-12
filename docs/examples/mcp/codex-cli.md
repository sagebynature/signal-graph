# Codex CLI example

Register Signal Graph as an MCP server in Codex:

```bash
codex mcp add signal-graph \\
  --env SIGNAL_GRAPH_PROJECT_DIR=/path/to/your/project \\
  -- /home/sachoi/signal-graph/.venv/bin/python -m signal_graph.mcp.server
```

Inspect the configured server:

```bash
codex mcp list --json
codex mcp get signal-graph --json
```
