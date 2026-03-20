# Analyst And Agent Guide

This guide is for discretionary analysts and coding agents using Signal Graph as a research workflow rather than as a codebase to extend.

If you need setup or environment help, read [`operator-guide.md`](operator-guide.md) first.

## Operating Principle

Run the CLI in this order:

`fetch` or `submit` -> `normalize` -> `research` -> `ingest` -> `rank` -> `explain`

Do not skip `research`. It is the provenance gate for downstream graph reasoning and memo output.

## Choose The Right Entry Point

- Use `submit` when you are manually entering an event note or hypothesis.
- Use `fetch` when you want a connector to return raw source items.
- Use `normalize` when you want to turn one raw item into a canonical event candidate.
- Use `research` when you want to attach evidence, contradictions, entity resolution, and confidence.
- Use `ingest` when the researched event is ready for graph reasoning.
- Use `rank` when you want likely instruments and timing windows.
- Use `explain` when you want a memo that separates fact, implication, and inference.

## Working With Real IDs

The examples below use placeholders such as `RAW_ITEM_ID`, `EVENT_CANDIDATE_ID`, and `GRAPH_EVENT_ID`.

In real use, capture the JSON output from each command and feed the returned ID into the next command.

## Standard Manual Workflow

```bash
uv run signal-graph submit --text "TSMC cuts capex"
uv run signal-graph normalize \
  --raw-item RAW_ITEM_ID \
  --event-type capex_cut \
  --direction negative \
  --primary-entity TSMC
uv run signal-graph research --event-candidate EVENT_CANDIDATE_ID --bundle-file bundle.json
uv run signal-graph ingest --event-candidate EVENT_CANDIDATE_ID
uv run signal-graph rank --event GRAPH_EVENT_ID
uv run signal-graph explain --event GRAPH_EVENT_ID --candidate SMH
```

## Standard Public-Web Workflow

The current `web` connector is intentionally lightweight. It returns stub public-web results but still exercises the same pipeline.

```bash
uv run signal-graph fetch --source web --query "chip export restriction"
uv run signal-graph normalize \
  --raw-item RAW_ITEM_ID \
  --event-type export_control \
  --direction negative \
  --primary-entity NVDA
uv run signal-graph research --event-candidate EVENT_CANDIDATE_ID --bundle-file bundle.json
uv run signal-graph ingest --event-candidate EVENT_CANDIDATE_ID
uv run signal-graph rank --event GRAPH_EVENT_ID
uv run signal-graph explain --event GRAPH_EVENT_ID --candidate SMH
```

## Research Bundle Shape

`research` reads a JSON file with the current bundle schema:

```json
{
  "supporting_documents": ["https://example.com/tsmc-capex"],
  "contradictions": ["Demand recovery may offset the capex cut."],
  "entity_resolution_results": {"TSMC": "company:TSMC"},
  "evidence_spans": ["TSMC said it would reduce capital spending."],
  "research_confidence": 0.7,
  "research_notes": "Capex cuts often pressure semiconductor equipment demand."
}
```

Field intent:

- `supporting_documents`: URLs or identifiers for source material
- `contradictions`: evidence or arguments that cut against the thesis
- `entity_resolution_results`: resolved entity mappings when you have them
- `evidence_spans`: short excerpts or findings that support the event framing
- `research_confidence`: numeric confidence for the bundle
- `research_notes`: freeform context worth preserving

Use `--allow-empty` only when you intentionally want a provenance shell with no attached evidence.

## Expected Outputs By Stage

- `submit` returns one persisted `RawSourceItem`
- `fetch` returns a JSON list of persisted `RawSourceItem` objects
- `normalize` returns an `EventCandidate` with `event_candidate_id`
- `research` returns a `ResearchBundle` keyed as `rb-<event_candidate_id>`
- `ingest` returns a `GraphEvent` with `graph_event_id`
- `rank` returns JSON candidates with scores, timing windows, matched entity, relationship path, and reason summary
- `explain` prints memo text and writes a markdown artifact under `.signal-graph/artifacts/`

## Provenance Rules

- Never claim a causal path without stored provenance and supporting records.
- Separate confirmed fact, graph implication, and analyst inference in written output.
- Prefer already stored local state before fetching new data.
- Treat contradictions as part of the research record, not as noise to hide.
- Do not present ranking output as trading advice. It is decision-support output.

## Local Policy Overrides

Operators can change ranking and memo behavior through `.signal-graph/config.toml` under `[scoring_policy]`.

What this can change:

- rank order
- timing windows
- reason-summary wording
- memo rationale text

If non-default local scoring policy is active, say so explicitly. The same event can rank differently across environments.

Reference example:

- [`../examples/scoring-policy.example.toml`](../examples/scoring-policy.example.toml)

## What Coding Agents Should Assume

- The CLI is the contract. Prefer explicit commands over direct database edits.
- Local state lives under `.signal-graph/`.
- SQLite is the source of truth for pipeline progress and provenance in this MVP.
- Neo4j is the reasoning layer, not the system of record for every object.
- The seeded reference graph is intentionally small: `TSMC`, `NVDA`, `AMD`, `ASML`, `INTC`, `SMH`, and `SOXX`.
- When in doubt, prefer deterministic local behavior over implicit network activity.

## Read Next

- Setup and troubleshooting: [`operator-guide.md`](operator-guide.md)
- Architecture and storage model: [`../architecture/system-overview.md`](../architecture/system-overview.md)
- Prompt templates: [`../prompts/signal-graph-analyst-prompt-pack.md`](../prompts/signal-graph-analyst-prompt-pack.md)
