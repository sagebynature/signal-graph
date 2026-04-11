---
evaluator:
  command: |
    python - <<'PY'
    from pathlib import Path
    import json
    base = Path('/home/sachoi/signal-graph/.omx/specs/autoresearch-signal-graph-agent-signal-journal')
    report = base / 'report.md'
    sources = base / 'sources.json'
    missing = []
    if not report.exists(): missing.append('report.md')
    if not sources.exists(): missing.append('sources.json')
    headings_missing = []
    source_count = 0
    source_keys_ok = True
    if report.exists():
        text = report.read_text()
        required = [
            '# Competitive Assessment',
            '# Recommended v1 Scope',
            '# Proposed Data Model Changes',
            '# Agent Integration Surface',
            '# Risks and Non-Goals',
            '# Source Notes',
        ]
        headings_missing = [heading for heading in required if heading not in text]
    if sources.exists():
        data = json.loads(sources.read_text())
        source_count = len(data) if isinstance(data, list) else -1
        if isinstance(data, list):
            for item in data:
                for key in ['title','url','kind','dateAccessed','notes']:
                    if key not in item:
                        source_keys_ok = False
                        break
        else:
            source_keys_ok = False
    status = 'pass' if not missing and not headings_missing and source_count >= 5 and source_keys_ok else 'fail'
    print(json.dumps({
        'status': status,
        'missingFiles': missing,
        'missingHeadings': headings_missing,
        'sourceCount': source_count,
        'sourceKeysOk': source_keys_ok
    }))
    PY
  format: json
  keep_policy: keep_all_artifacts
---

# Sandbox — signal-graph-agent-signal-journal

## Working directory
`/home/sachoi/signal-graph`

## Allowed evidence sources
- Local repository files under this repo
- GBrain repository/docs
- MemPalace repository/docs
- GitHubAwesome article dated **December 14, 2025** for trend context
- Other primary project documentation directly relevant to agent-memory / provenance / graph-recall positioning

## Required output files
Create or overwrite:
- `.omx/specs/autoresearch-signal-graph-agent-signal-journal/report.md`
- `.omx/specs/autoresearch-signal-graph-agent-signal-journal/sources.json`

## Source recording contract
`sources.json` must be a JSON array. Each item must include:
- `title`
- `url`
- `kind`
- `dateAccessed`
- `notes`

## Guardrails
- Do not implement code changes in this research run.
- Do not broaden v1 beyond the locked non-goals.
- Do not rename the product away from Signal Graph.
- Distinguish repo-grounded evidence from inference.
- Favor concise evidence with direct planning implications.
