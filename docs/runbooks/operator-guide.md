# Operator Guide

This guide covers the supported local runtime workflow for Signal Graph: environment validation, bootstrap discovery, signal capture/journaling/recall, automation helpers, and MCP startup.

## Environment

Required local tools:

- Python 3.12
- `uv`
- Docker
- Neo4j runtime availability

## Bootstrap

Verify prerequisites and initialize local state:

```bash
uv run signal-graph doctor --json
uv run signal-graph init
uv run signal-graph bootstrap-describe --format markdown
```

`signal-graph doctor` is non-destructive. It validates runtime readiness, local config parsing, and Neo4j auth formatting.

## Operational Automation

Signal Graph exposes host-facing automation guidance through `automation-describe` and the integration commands.

```bash
uv run signal-graph automation-describe --format markdown
uv run signal-graph integration-install --host claude-code
uv run signal-graph integration-audit --host claude-code --json
uv run signal-graph integration-uninstall --host claude-code
```

## Neo4j Runtime

Signal journaling depends on a reachable Neo4j runtime.

```bash
docker compose up -d neo4j
```

If journaling fails, fix Neo4j before debugging Signal Graph application code.

## Manual Smoke Test

```bash
uv run signal-graph init
signal_id=$(uv run signal-graph capture-signal           --text "Operator smoke signal for deployment readiness."           --origin-type user           --source-name manual           --what deployment           --where notes/deploy.md | uv run python -c 'import json,sys; print(json.load(sys.stdin)["signal_id"])')
uv run signal-graph journalize-signal --signal "$signal_id"
uv run signal-graph recall-signal --query deployment
```

Expected outcomes:

- `capture-signal` returns stable JSON with a `signal_id`
- `journalize-signal` returns a `graph_path` and `journaled_at`
- `recall-signal` returns structured JSON and writes a markdown artifact under `.signal-graph/artifacts/`

## MCP Startup

Supported launch paths:

```bash
uv run signal-graph mcp-server
uv run signal-graph-mcp
```

See `docs/integrations/README.md` for host matrix details and config examples.

## Repository Responsibilities

The supported repository surfaces are:

- local bootstrap and automation discovery
- signal capture, graph journaling, and recall
- MCP startup and host integration validation
- local artifacts and inspectable state

## Troubleshooting

- `signal-graph doctor` fails: fix missing runtime tooling or config errors first.
- `capture-signal` fails: check the local project was initialized and the payload is valid.
- `journalize-signal` fails: verify Neo4j is reachable.
- `recall-signal` returns no matches: confirm signals were captured and journaled for the query or filters you are using.
- integration commands drift from docs: compare with `automation-describe` and `bootstrap-describe` output.
