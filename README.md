# trade-graph

## Bootstrap

- Install dependencies with `uv sync`.
- Run tests with `uv run pytest`.
- Run the CLI with `uv run trade-graph version`.
- Verify the local toolchain with `uv run trade-graph doctor`.
- Initialize local state with `uv run trade-graph init`.
- Set `NEO4J_AUTH` before the first `make neo4j-up` if you want a non-default `neo4j/<password>` credential.
- If you change `NEO4J_AUTH` later, remove `./infra/neo4j/data` first or keep using the existing password.
- Removing `./infra/neo4j/data` also deletes your persisted local Neo4j data.
- Authless mode such as `NEO4J_AUTH=none` is not part of this bootstrap setup.
- Start Neo4j with `make neo4j-up`.
- Wait for the container to become `healthy` in `docker compose ps` before connecting.
- Stop Neo4j with `make neo4j-down`.
- Neo4j data, logs, and plugins live under `./infra/neo4j/`.

## Pipeline

- Command order: `fetch` or `submit` -> `normalize` -> `research` -> `ingest` -> `rank` -> `explain`.
- Provenance should be established during `research` before ranking or explanation claims are made.
- See `docs/runbooks/agent-usage.md` and `docs/runbooks/local-development.md` for concrete examples.
