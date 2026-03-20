# Agent Usage

Use the CLI in a strict pipeline order so every downstream step has stored local state to work from.

```bash
uv run trade-graph submit --text "TSMC cuts capex"
uv run trade-graph normalize --raw-item raw-123
uv run trade-graph research --event-candidate evt-123
uv run trade-graph ingest --event-candidate evt-123
uv run trade-graph rank --event ge-123
uv run trade-graph explain --event ge-123 --candidate SMH
```

Guidelines:

- Start with `submit` for manual inputs or `fetch` for connector-driven raw items.
- Do not skip `research`; it is the provenance gate for downstream graph steps.
- Use `explain` only after ingest and rank have produced a concrete event and candidate pair.
