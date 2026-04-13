# Memory V2 Redaction Behavior

This runbook describes the bounded V2 redaction slice.

## Contract

- `Redaction{redaction_id, owner_id, target_id, reason, created_at}`
- persisted separately under `redactions/<id>.json`
- surfaced in:
  - `QueryResult.applied_redactions`
  - `ExplanationResponse.active_redactions`
  - `ExplanationResponse.is_redacted`

## MCP parity

- stdio tool: `memory_redact`
- HTTP route: `POST /tools/memory_redact`

## Deterministic behavior

1. duplicate redactions dedupe by `owner + target + reason`
2. redacted targets disappear from `memory_query`
3. `memory_explain` on a redacted event returns:
   - `action_text = "[redacted]"`
   - empty provenance/evidence
   - `is_redacted = true`
   - guidance prefixed with the stored reason
4. correction remains distinct from redaction
