.PHONY: test typecheck doctor neo4j-up neo4j-down

test:
	uv run pytest

typecheck:
	uv run ty check

doctor:
	uv run trade-graph doctor

neo4j-up:
	mkdir -p infra/neo4j/data infra/neo4j/logs infra/neo4j/plugins
	docker compose up -d neo4j

neo4j-down:
	docker compose stop neo4j
