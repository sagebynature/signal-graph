# Local Development

Core verification commands:

```bash
uv run pytest -v
uv run ty check
uv run trade-graph doctor
uv run trade-graph init
uv run trade-graph version
```

Manual end-to-end smoke test:

```bash
uv run trade-graph submit --text "TSMC cuts capex"
uv run trade-graph normalize --raw-item raw-123
uv run trade-graph research --event-candidate evt-123
uv run trade-graph ingest --event-candidate evt-123
uv run trade-graph rank --event ge-123
uv run trade-graph explain --event ge-123 --candidate SMH
```
