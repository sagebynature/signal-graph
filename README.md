# Signal Graph

`Signal Graph` is being rewritten as a local, provenance-aware **memory and decision-support system** for humans and AI tools.

The favored V2 direction keeps the CLI/MCP operating model but shifts the product center from event-driven trading research to **owner-scoped memory capture, retrieval, explanation, correction, and artifact recall**. The current repository still contains the V1 trading-research workflow while the V2 rewrite is being built inside this repo.

V2 is designed for a workflow where a person and one or more AI actors:

1. establish owner and actor identity,
2. capture hooks, shared artifacts, and session context,
3. preserve raw evidence canonically,
4. derive graph-backed interpretations and explanations with confidence-labeled `why`,
5. query prior decisions by who/topic/date, and
6. record corrections or redactions with deterministic downstream effects.

The product remains intentionally terminal-native. It favors explicit commands, local state, deterministic artifacts, and machine-readable output over a dashboard-first experience.

## What This Repo Is

This repository currently contains both the brownfield V1 runtime and the V2 rewrite track:

- a `signal-graph` CLI and `signal-graph-mcp` entrypoint
- local SQLite and Neo4j infrastructure used by the existing runtime
- filesystem artifacts, integration examples, and runbooks for operators and coding agents
- approved V2 rewrite plans, documentation, and ADRs that define the target memory-system shape

## Intended Users

- Developers and operators extending the local runtime
- Humans who want a trustworthy memory layer for AI-assisted work
- AI tools that need a strict, auditable capture/retrieval contract
- Stakeholders validating the V2 product direction, storage model, and trust boundaries

## Core Use Cases

- Capture AI-tool hooks with explicit owner, actor, and session provenance
- Preserve shared documents, folders, and other raw artifacts without mutating source truth
- Query prior actions, decisions, and evidence by who, topic, or date
- Explain why an action or recommendation happened with provenance and confidence labeling
- Record corrections/redactions that deterministically change downstream retrieval behavior
- Continue operating the legacy V1 event-to-thesis workflow while the rewrite is in flight

## Workflow

The V2 canonical loop is:

`owner/actor setup -> hook/share/capture -> append-only event + raw artifact storage -> projection/indexing -> query/explain -> correction/redaction`

The important operating rule is that Signal Graph should preserve **who / what / when / where** by default and only persist **why** when it is explicit or clearly labeled as inference.

The brownfield V1 workflow that still ships in this repo is:

`fetch` or `submit` -> `normalize` -> `research` -> `ingest` -> `rank` -> `explain`

The journal pipeline remains available while the rewrite proceeds:

`capture-signal` -> `journalize-signal` -> `recall-signal`

Stage 2 recall now supports:
- quoted exact phrases, for example `--query '"deployment checklist"'`
- provenance-aware filters such as `--origin-type`, `--session-id`, `--runtime-family`, and `--source-name`
- multiple recall views via `--view ranked|timeline|session`
- richer explanation payloads describing why each match ranked where it did

For MCP clients, the repo already ships an stdio server surface:

```bash
uv run signal-graph mcp-server
# or
uv run signal-graph-mcp
```

## Quick Start

### Bootstrap

```bash
uv sync
uv run signal-graph bootstrap-describe
uv run signal-graph doctor
uv run signal-graph init
uv run signal-graph version
```

`signal-graph doctor` is non-destructive. It checks runtime readiness for the local workflow, verifies that `.signal-graph/config.toml` is parseable when present, and rejects malformed `NEO4J_AUTH` values. The config file is optional.

### Agent Bootstrap Contract

Agents should start with the runtime-owned bootstrap contract:

```bash
uv run signal-graph bootstrap-describe
```

This returns a versioned machine-readable contract with:
- entrypoints
- prerequisites and environment expectations
- the minimum smoke path
- expected proof outputs
- MCP startup assumptions
- next recommended actions

### Agent Operational Automation

For validated hosts, Signal Graph can also describe and manage operational automation workflows:

```bash
uv run signal-graph automation-describe
uv run signal-graph integration-install --host claude-code
uv run signal-graph integration-audit --host claude-code --json
uv run signal-graph integration-uninstall --host claude-code
```

The first wave is intentionally limited to validated hosts only:
- `claude-code`
- `codex-cli`

### Local Neo4j

- Set `NEO4J_AUTH` before the first `make neo4j-up` if you want a non-default `neo4j/<password>` credential.
- `NEO4J_AUTH` must use the `username/password` format with non-empty values.
- If you change `NEO4J_AUTH` later, remove `./infra/neo4j/data` first or keep using the existing password.
- Removing `./infra/neo4j/data` also deletes your persisted local Neo4j data.
- Authless mode such as `NEO4J_AUTH=none` is not part of this bootstrap setup.

```bash
make neo4j-up
docker compose ps
make neo4j-down
```

Neo4j data, logs, and plugins live under `./infra/neo4j/`.

### Minimal Manual Flow

Create a research bundle first:

```bash
cat > bundle.json <<'JSON'
{
  "supporting_documents": ["https://example.com/tsmc-capex"],
  "contradictions": ["Demand recovery may offset the capex cut."],
  "entity_resolution_results": {"TSMC": "company:TSMC"},
  "evidence_spans": ["TSMC said it would reduce capital spending."],
  "research_confidence": 0.7,
  "research_notes": "Capex cuts often pressure semiconductor equipment demand."
}
JSON
```

Then run the pipeline with real captured ids:

```bash
uv run signal-graph init
uv run python - <<'PY'
from signal_graph.graph.client import GraphClient
from signal_graph.graph.schema import demo_reference_graph_statements

client = GraphClient()
try:
    client.run_in_transaction(demo_reference_graph_statements())
finally:
    client.close()
PY
raw_item_id=$(uv run signal-graph submit --text "TSMC cuts capex" | uv run python -c 'import json,sys; print(json.load(sys.stdin)["raw_item_id"])')
event_candidate_id=$(uv run signal-graph normalize --raw-item "$raw_item_id" --event-type capex_cut --direction negative --primary-entity TSMC | uv run python -c 'import json,sys; print(json.load(sys.stdin)["event_candidate_id"])')
uv run signal-graph research --event-candidate "$event_candidate_id" --bundle-file bundle.json
graph_event_id=$(uv run signal-graph ingest --event-candidate "$event_candidate_id" | uv run python -c 'import json,sys; print(json.load(sys.stdin)["graph_event_id"])')
uv run signal-graph rank --event "$graph_event_id"
uv run signal-graph explain --event "$graph_event_id" --candidate SMH
```

`research` now expects either `--bundle-file` or an explicit `--allow-empty`. Empty placeholder bundles are no longer the default.

The reference graph load step is explicit. Normal `ingest` no longer seeds demo instruments automatically. Without reference data, rank output will be limited to instruments that already exist in Neo4j.

For a fully isolated, copy-pasteable smoke path that keeps state in a temp directory, use [`docs/runbooks/runnable-smoke-test.md`](docs/runbooks/runnable-smoke-test.md).

### Connector Reality

- `fetch --source web` currently returns a deterministic demo item backed by `example.com`; it is not live public-web retrieval.
- `fetch --source premium` is currently disabled and exits with a clear placeholder message.
- The seeded demo ranking universe is intentionally small: `TSMC`, `NVDA`, `AMD`, `ASML`, `INTC`, `SMH`, and `SOXX`.

### Customizing Scoring Policy

Scoring policy can be customized locally in `.signal-graph/config.toml`. The file is optional. When present, it must be valid TOML; malformed or unreadable config is not silently ignored. `signal-graph doctor` reports these config problems explicitly, and other commands that load config currently raise an error when they encounter them. The system keeps its built-in defaults, then merges local overrides by exact match:

- path rule match key: `relationship_path`
- event override match key: `event_type + direction + relationship_path`
- event fallback rationale match key: `event_type + direction`

Example:

```toml
[scoring_policy]

[[scoring_policy.events]]
event_type = "export_control"
direction = "negative"
fallback_rationale = "For a negative `export_control`, the model emphasizes instruments that move with immediate market access risk."

[[scoring_policy.events.overrides]]
relationship_path = ["HOLDS"]
base_score = 0.64
timing_window = "immediate"
rationale = "For a negative `export_control`, sector ETF exposure can move immediately."
```

Use the full example file at `docs/examples/scoring-policy.example.toml` as the copyable reference.

## Documentation Map

Start with [`docs/README.md`](docs/README.md) for the full documentation guide.

- Stakeholder or product reader: [`docs/overview/product.md`](docs/overview/product.md)
- Architecture reader: [`docs/architecture/system-overview.md`](docs/architecture/system-overview.md)
- Local developer or operator: [`docs/runbooks/operator-guide.md`](docs/runbooks/operator-guide.md)
- Analyst or coding agent user: [`docs/runbooks/analyst-agent-guide.md`](docs/runbooks/analyst-agent-guide.md)
- Runnable onboarding and smoke test: [`docs/runbooks/runnable-smoke-test.md`](docs/runbooks/runnable-smoke-test.md)
- Reusable prompt templates: [`docs/prompts/signal-graph-analyst-prompt-pack.md`](docs/prompts/signal-graph-analyst-prompt-pack.md)

Decision records:

- [`docs/adr/ADR-0001-cli-first-provenance-workflow.md`](docs/adr/ADR-0001-cli-first-provenance-workflow.md)
- [`docs/adr/ADR-0002-sqlite-plus-neo4j-separation.md`](docs/adr/ADR-0002-sqlite-plus-neo4j-separation.md)
- [`docs/adr/ADR-0003-agent-skill-and-command-order.md`](docs/adr/ADR-0003-agent-skill-and-command-order.md)
- [`docs/adr/ADR-0004-v2-memory-ontology.md`](docs/adr/ADR-0004-v2-memory-ontology.md)
- [`docs/adr/ADR-0005-v2-storage-of-record-split.md`](docs/adr/ADR-0005-v2-storage-of-record-split.md)
- [`docs/adr/ADR-0006-v2-mcp-transport-parity.md`](docs/adr/ADR-0006-v2-mcp-transport-parity.md)
- [`docs/adr/ADR-0007-v2-hook-ingestion-envelope.md`](docs/adr/ADR-0007-v2-hook-ingestion-envelope.md)
- [`docs/adr/ADR-0008-v2-http-trusted-environment-boundary.md`](docs/adr/ADR-0008-v2-http-trusted-environment-boundary.md)

Legacy plan and design material:

- [`docs/plans/2026-03-19-neo4j-ai-trading-design.md`](docs/plans/2026-03-19-neo4j-ai-trading-design.md)
- [`docs/plans/2026-03-19-neo4j-ai-trading-mvp.md`](docs/plans/2026-03-19-neo4j-ai-trading-mvp.md)

Older planning documents may still refer to `trade-graph`; they describe the same project before the rebrand to `Signal Graph`.

## Current State

The repository currently provides:

- the existing V1 local CLI commands for `doctor`, `init`, `submit`, `fetch`, `normalize`, `research`, `ingest`, `rank`, and `explain`
- journal signal capture plus MCP-backed recall commands for preserving user/agent provenance
- an stdio MCP surface today, with HTTP parity tracked as a V2 rewrite deliverable
- approved V2 docs and ADRs for the owner/actor ontology, storage-of-record split, hook event envelope, transport parity, and trusted-environment HTTP boundary
- a brownfield integration base for moving from trading-research workflows toward owner-scoped memory and decision support

This is **not yet** the finished V2 memory system. It is the active rewrite workspace plus the still-operational V1 runtime.

## Non-Goals For This Cut

- automated execution or brokerage integration
- public multi-tenant SaaS hosting for the HTTP transport
- opaque recommendation generation that bypasses stored provenance
- silent capture of inferred preferences or corrective rules without confirmation
- mutating raw artifact truth in order to revise derived interpretations

## Development Verification

```bash
uv run python -m pytest -v
uv run ty check
uv run signal-graph doctor
uv run signal-graph version
```

`uv run ty check` remains a contributor verification step. `signal-graph doctor` does not require `ty` to be installed.
