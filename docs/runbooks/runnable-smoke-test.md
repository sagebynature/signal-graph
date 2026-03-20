# Runnable Smoke Test

This is the copy-pasteable onboarding flow for a clean temp directory with a local Neo4j instance already available.

It keeps `.signal-graph/` state out of the repo checkout by using `uv run --project "$repo_root" ...` from a fresh temporary directory.

## Reality Check

- `fetch --source web` is currently a deterministic demo stub backed by `example.com`, not live public-web retrieval.
- `fetch --source premium` is currently disabled and exits with a clear placeholder message.
- `rank` only returns tradable instruments already present in Neo4j. This smoke test explicitly loads the small demo reference universe before ranking.

## Manual Event Flow

Run these commands from the repository root.

```bash
repo_root=$(pwd)
tmp_dir=$(mktemp -d)
cd "$tmp_dir"

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

uv run --project "$repo_root" signal-graph doctor
uv run --project "$repo_root" signal-graph init
uv run --project "$repo_root" python - <<'PY'
from signal_graph.graph.client import GraphClient
from signal_graph.graph.schema import demo_reference_graph_statements

client = GraphClient()
try:
    client.run_in_transaction(demo_reference_graph_statements())
finally:
    client.close()
PY

raw_item_id=$(uv run --project "$repo_root" signal-graph submit --text "TSMC cuts capex" | uv run --project "$repo_root" python -c 'import json,sys; print(json.load(sys.stdin)["raw_item_id"])')
echo "raw_item_id=$raw_item_id"

event_candidate_id=$(uv run --project "$repo_root" signal-graph normalize --raw-item "$raw_item_id" --event-type capex_cut --direction negative --primary-entity TSMC | uv run --project "$repo_root" python -c 'import json,sys; print(json.load(sys.stdin)["event_candidate_id"])')
echo "event_candidate_id=$event_candidate_id"

uv run --project "$repo_root" signal-graph research --event-candidate "$event_candidate_id" --bundle-file bundle.json

graph_event_id=$(uv run --project "$repo_root" signal-graph ingest --event-candidate "$event_candidate_id" | uv run --project "$repo_root" python -c 'import json,sys; print(json.load(sys.stdin)["graph_event_id"])')
echo "graph_event_id=$graph_event_id"

uv run --project "$repo_root" signal-graph rank --event "$graph_event_id"
uv run --project "$repo_root" signal-graph explain --event "$graph_event_id" --candidate SMH
```

## Demo Web Fetch Flow

Use this only to validate the CLI path. The fetched item is stub content, not live web data.

```bash
repo_root=$(pwd)
tmp_dir=$(mktemp -d)
cd "$tmp_dir"

cat > bundle.json <<'JSON'
{
  "supporting_documents": ["https://example.com/export-control"],
  "contradictions": ["Scope could narrow before enforcement."],
  "entity_resolution_results": {"NVDA": "company:NVDA"},
  "evidence_spans": ["Officials said additional export controls are under review."],
  "research_confidence": 0.6,
  "research_notes": "Use this flow only to validate CLI wiring, not source quality."
}
JSON

uv run --project "$repo_root" signal-graph init
uv run --project "$repo_root" python - <<'PY'
from signal_graph.graph.client import GraphClient
from signal_graph.graph.schema import demo_reference_graph_statements

client = GraphClient()
try:
    client.run_in_transaction(demo_reference_graph_statements())
finally:
    client.close()
PY

raw_item_id=$(uv run --project "$repo_root" signal-graph fetch --source web --query "chip export restriction" | uv run --project "$repo_root" python -c 'import json,sys; items=json.load(sys.stdin); print(items[0]["raw_item_id"])')
event_candidate_id=$(uv run --project "$repo_root" signal-graph normalize --raw-item "$raw_item_id" --event-type export_control --direction negative --primary-entity NVDA | uv run --project "$repo_root" python -c 'import json,sys; print(json.load(sys.stdin)["event_candidate_id"])')
uv run --project "$repo_root" signal-graph research --event-candidate "$event_candidate_id" --bundle-file bundle.json
graph_event_id=$(uv run --project "$repo_root" signal-graph ingest --event-candidate "$event_candidate_id" | uv run --project "$repo_root" python -c 'import json,sys; print(json.load(sys.stdin)["graph_event_id"])')
uv run --project "$repo_root" signal-graph rank --event "$graph_event_id"
uv run --project "$repo_root" signal-graph explain --event "$graph_event_id" --candidate SMH
```
