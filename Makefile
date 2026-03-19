.PHONY: test typecheck doctor

test:
	uv run pytest

typecheck:
	uv run ty check

doctor:
	uv run trade-graph doctor
