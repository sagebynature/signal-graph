# Analyst And Agent Guide

This guide is for discretionary analysts and coding agents using the CLI as an operating workflow rather than extending the codebase.

## Operating Principle

Use the CLI in a strict pipeline order so every downstream step has stored local state to work from:

`fetch` or `submit` -> `normalize` -> `research` -> `ingest` -> `rank` -> `explain`

Do not skip `research`. It is the provenance gate for downstream graph and memo steps.

## When To Use Which Entry Point

- Use `submit` when a human or agent is manually capturing an event hypothesis
- Use `fetch` when a connector can return raw source items
- Use `normalize` to convert raw source text into a canonical event candidate
- Use `research` to attach supporting evidence, contradictions, and confidence context
- Use `ingest` when the event is ready for graph-oriented reasoning
- Use `rank` to get candidate instruments and timing windows
- Use `explain` to write a memo with clear provenance boundaries

## Standard Manual Workflow

```bash
uv run signal-graph init
uv run signal-graph submit --text "TSMC cuts capex"
uv run signal-graph normalize --raw-item raw-123
uv run signal-graph research --event-candidate evt-123
uv run signal-graph ingest --event-candidate evt-123
uv run signal-graph rank --event ge-123
uv run signal-graph explain --event ge-123 --candidate SMH
```

## Standard Public Web Workflow

```bash
uv run signal-graph init
uv run signal-graph fetch --source web --query "chip export restriction"
uv run signal-graph normalize --raw-item raw-web-123
uv run signal-graph research --event-candidate evt-123
uv run signal-graph ingest --event-candidate evt-123
uv run signal-graph rank --event ge-123
uv run signal-graph explain --event ge-123 --candidate SMH
```

## Provenance Rules

- Never claim a causal path without stored provenance and supporting source records
- Separate confirmed fact, graph implication, and assistant inference in written output
- Prefer already ingested local events before fetching new data
- Treat contradictions as part of the research record, not as noise to hide
- Avoid presenting ranking output as trading advice; it is decision-support input

## Expected Outputs

- `submit` and `fetch` return raw-source-item shaped JSON data
- `normalize` returns an event candidate
- `research` returns a research bundle
- `ingest` returns a graph event record
- `rank` returns ranked candidates with scores and timing windows
- `explain` prints memo text and writes a markdown artifact under `.signal-graph/artifacts/`

## What Coding Agents Should Assume

- The CLI is the contract; use explicit commands instead of poking the database directly
- Local state lives under `.signal-graph/`
- SQLite is the source of truth for pipeline progress and provenance artifacts in this MVP
- Neo4j is the reasoning layer, not the system of record for every object
- When in doubt, favor deterministic local behavior over implicit network activity
