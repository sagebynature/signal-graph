# signal-graph

Use this skill when operating the local trading research pipeline.

- Never claim a causal path without stored provenance and supporting sources.
- Distinguish confirmed fact, graph implication, and assistant inference in every memo.
- Prefer already ingested local events before running a new live fetch.
- Use the command order: `fetch` or `submit` -> `normalize` -> `research` -> `ingest` -> `rank` -> `explain`.
- Treat `research` as the provenance checkpoint before any graph ingest or ranking claim.
