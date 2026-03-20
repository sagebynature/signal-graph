---
name: signal-graph
description: Operate the local Signal Graph trading-research toolkit through its supported CLI workflow. Use when an agent needs to analyze a market event, capture or fetch source items, normalize them into event candidates, attach provenance-backed research, ingest them into the graph layer, rank likely instruments or ETFs, write memo output, adapt analyst prompts, or troubleshoot local Signal Graph runtime and workflow issues.
---

# Signal Graph

Use Signal Graph as a CLI-first, provenance-aware trading research pipeline.

Treat the CLI as the contract. Prefer explicit `uv run signal-graph ...` commands over direct database edits or ad hoc local state changes.

## Working Model

Understand the tool before operating it:

- Signal Graph is a local research toolkit, not an execution engine or autonomous trading system.
- SQLite under `.signal-graph/` is the local system of record for pipeline progress and provenance.
- Neo4j is the graph reasoning layer used after research is attached.
- Memo artifacts are written to `.signal-graph/artifacts/`.
- The pipeline exists to turn raw market events into explainable trade candidates with explicit provenance boundaries.

Read `../../docs/README.md` if you need the human-facing documentation map before operating the repo.

## Command Contract

Run commands in this order:

`fetch` or `submit` -> `normalize` -> `research` -> `ingest` -> `rank` -> `explain`

Follow these rules:

- Do not skip `research`. It is the provenance gate for downstream graph and memo steps.
- Prefer already persisted local events before performing a new live fetch.
- Distinguish confirmed fact, graph implication, and assistant inference in every written explanation.
- Treat contradictions as part of the record, not noise to suppress.
- Avoid presenting rank output as trading advice. It is decision-support output.

## Analyst Prompting Pattern

When the user wants research output rather than low-level CLI help, structure the task the same way the analyst prompt pack does.

Base operating pattern:

- capture or locate the source item
- normalize it into a clean event candidate
- attach supporting evidence, contradictions, and confidence context
- ingest for graph reasoning
- rank candidate expressions
- produce a memo

Default final-output contract:

- `Event Record`: event summary, primary entity, event type, direction, confirmed facts, unresolved assumptions
- `Evidence And Contradictions`: supporting evidence with provenance, contradictory evidence, research confidence
- `Ranked Candidates`: ticker, name, score or relative rank, timing window, matched entity, relationship path, short reason summary
- `Memo`: separate `Confirmed Facts`, `Graph Implications`, and `Analyst Inference`

If the user needs prompt wording or reusable analyst prompts, read `../../docs/prompts/signal-graph-analyst-prompt-pack.md` and reuse its base prompt plus the closest task module.

Map common analyst intents to these modes:

- rapid first pass -> `Rapid Triage`
- second-order names or ETF exposure -> `Spillover Map`
- fresh headline with uncertainty -> `Breaking News Review`
- contested thesis -> `Bull vs Bear Case`
- side-by-side event framing -> `Compare Two Narratives`
- ETF-focused expression -> `ETF Read-Through`
- reuse stored work -> `Existing Research Replay`
- sparse or suspicious output -> `Weak Signal Diagnosis`
- scoring-policy comparison -> `Policy Sensitivity Check`
- chain integrity check -> `Provenance Audit`
- senior-reader summary -> `Executive Summary Memo`

## Stage Guide

Use `submit` when a human or agent is manually entering an event hypothesis.

Use `fetch` when a connector can return raw source items. Expect connector coverage to remain limited in this cut. The `web` connector returns stub public-web results and the `premium` connector is still a placeholder.

Use `normalize` to convert a raw item into a canonical event candidate. Provide `--event-type`, `--direction`, and `--primary-entity`; use `--secondary-entity` when the event needs it.

Use `research` to attach supporting documents, contradictions, entity resolution results, evidence spans, confidence, and research notes. Prefer `--bundle-file`; use `--allow-empty` only when you intentionally want a provenance shell with no supporting bundle.

Use `ingest` only after the event candidate and research bundle exist. This writes the graph event and sends the payload into the Neo4j layer.

Use `rank` to get candidate instruments, scores, timing windows, relationship paths, and reason summaries.

Use `explain` to print a memo and write a markdown artifact that separates fact, implication, and inference.

## Operating Defaults

Bootstrap with:

```bash
uv sync --group dev
uv run signal-graph doctor
uv run signal-graph init
uv run signal-graph version
```

If the `signal-graph` command is unavailable, recover the environment before doing pipeline work:

```bash
git clone git@github.com:schoi80/signal-graph.git
cd signal-graph
uv sync --group dev
uv run signal-graph doctor
uv run signal-graph init
```

Install and start the local Neo4j dependency through Docker:

```bash
make neo4j-up
docker compose ps
```

Assume these prerequisites for a usable local environment:

- Python 3.12
- `uv`
- `ty`
- Docker
- `make`

If Neo4j is not available yet, do not attempt `ingest`, `rank`, or `explain` and then guess at downstream results. Bring the dependency up first or stop and report the environment gap.

Use this minimal flow for a manual event. Replace placeholder IDs with values returned by the preceding command.

```bash
uv run signal-graph submit --text "TSMC cuts capex"
uv run signal-graph normalize --raw-item RAW_ITEM_ID --event-type capex_cut --direction negative --primary-entity TSMC
uv run signal-graph research --event-candidate EVENT_CANDIDATE_ID --bundle-file bundle.json
uv run signal-graph ingest --event-candidate EVENT_CANDIDATE_ID
uv run signal-graph rank --event GRAPH_EVENT_ID
uv run signal-graph explain --event GRAPH_EVENT_ID --candidate SMH
```

Assume local state lives under `.signal-graph/`. Inspect `.signal-graph/signal_graph.db` and `.signal-graph/artifacts/` before inventing alternate storage paths.

## Local Policy And Runtime Caveats

Check `.signal-graph/config.toml` before comparing ranking or memo results across machines. Local scoring-policy overrides can change rank order, timing windows, reason summaries, and memo rationale text.

Use `make neo4j-up` and `make neo4j-down` to manage the local Neo4j runtime. If Neo4j auth changes unexpectedly, inspect `NEO4J_AUTH` and the persisted data under `infra/neo4j/data`.

If ranking looks empty or weak, do not assume the graph should already contain the needed entities or relationships. Start from the possibility of a fresh local graph and check, in order:

- whether the event framing is specific enough
- whether the primary entity resolves cleanly
- whether the research bundle contains actual evidence and contradictions
- whether local graph state is missing the needed coverage
- whether local scoring policy is distorting the result

Use the same root-cause style as `Weak Signal Diagnosis`: explain the failure mode in plain English before rerunning or changing the workflow.

## Read More Only When Needed

Read `../../docs/README.md` when you need the full documentation map and role-based reading order.

Read `../../docs/runbooks/analyst-agent-guide.md` when operating the pipeline as an analyst or agent.

Read `../../docs/prompts/signal-graph-analyst-prompt-pack.md` when the task is prompt design, analyst workflow guidance, memo-shape guidance, or event-analysis framing.

Read `../../docs/runbooks/operator-guide.md` when debugging environment, Neo4j, or local config issues.

Read `../../docs/architecture/system-overview.md` when reasoning about SQLite, Neo4j, filesystem artifacts, and service boundaries.

Read `../../docs/adr/ADR-0003-agent-skill-and-command-order.md` when validating why the command order and provenance guardrails are strict.
