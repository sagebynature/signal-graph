# Operator Guide

This guide is for developers and local operators working inside the repository.

## Environment

- Python 3.12
- `uv` for dependency and command execution
- `ty` for type checks
- Docker for the local Neo4j runtime
- `make` for common workflows

## Bootstrap

```bash
uv sync
uv run signal-graph doctor
uv run signal-graph init
uv run signal-graph version
```

## Neo4j Runtime

Before first startup, set `NEO4J_AUTH` if you do not want the default `neo4j/<password>` credential.

```bash
make neo4j-up
docker compose ps
make neo4j-down
```

Operational notes:

- wait for the container to become `healthy` before connecting
- `./infra/neo4j/data` holds persisted database state
- removing `./infra/neo4j/data` also removes local graph state
- if you change `NEO4J_AUTH`, you may need to clear `./infra/neo4j/data` or keep using the existing password

## Common Verification Commands

```bash
uv run pytest -v
uv run ty check
uv run signal-graph doctor
uv run signal-graph version
```

## Manual Smoke Test

```bash
uv run signal-graph init
uv run signal-graph submit --text "TSMC cuts capex"
uv run signal-graph normalize --raw-item raw-123
uv run signal-graph research --event-candidate evt-123
uv run signal-graph ingest --event-candidate evt-123
uv run signal-graph rank --event ge-123
uv run signal-graph explain --event ge-123 --candidate SMH
```

## Repository Responsibilities

- `src/signal_graph/cli/`: CLI entrypoints and command surface
- `src/signal_graph/services/`: pipeline logic
- `src/signal_graph/models/`: canonical data models
- `src/signal_graph/storage/`: local SQLite access and schema
- `src/signal_graph/graph/`: graph client and schema helpers
- `tests/`: CLI, storage, docs, and end-to-end verification

## Troubleshooting

- `signal-graph doctor` fails: install missing tooling before debugging application code
- Neo4j auth mismatch: either keep the existing password or reset the local data directory
- Unexpected local state: inspect `.signal-graph/signal_graph.db` and `.signal-graph/artifacts/`
- Smoke test drift: run `uv run pytest -v` first, then reproduce the failing CLI step manually
