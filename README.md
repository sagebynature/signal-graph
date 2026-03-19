# trade-graph

## Bootstrap

- Install dependencies with `uv sync`.
- Run tests with `uv run pytest`.
- Run the CLI with `uv run trade-graph version`.
- Set `NEO4J_AUTH` before the first `make neo4j-up` if you want a non-default `neo4j/<password>` credential.
- If you change `NEO4J_AUTH` later, remove `./infra/neo4j/data` first or keep using the existing password.
- Removing `./infra/neo4j/data` also deletes your persisted local Neo4j data.
- Authless mode such as `NEO4J_AUTH=none` is not part of this bootstrap setup.
- Start Neo4j with `make neo4j-up`.
- Wait for the container to become `healthy` in `docker compose ps` before connecting.
- Stop Neo4j with `make neo4j-down`.
- Neo4j data, logs, and plugins live under `./infra/neo4j/`.
