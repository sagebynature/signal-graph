.PHONY: test typecheck doctor install-hooks neo4j-up neo4j-down

test: typecheck
	uv run python -m pytest

typecheck:
	uv run ty check

doctor:
	uv run signal-graph doctor

install-hooks:
	uv run pre-commit install --install-hooks --hook-type pre-commit --hook-type commit-msg

neo4j-up:
	mkdir -p infra/neo4j/data infra/neo4j/logs infra/neo4j/plugins
	docker compose up -d neo4j

neo4j-down:
	docker compose stop neo4j
