# ADR-0003: Encode Agent Usage Through Skill Rules And Command Order

## Status

Accepted

## Context

The repository is intended to be operated not only by humans but also by coding agents. Agents need more than API access; they need a safe workflow contract that says what order to run commands in, what artifacts matter, and where inference must stop.

## Decision Drivers

- safe agent operation
- predictable workflow execution
- provenance discipline
- low ambiguity in local automation

## Considered Options

### Option 1: Let Agents Infer Workflow From Source Code

- Pros: no extra documentation burden
- Cons: unsafe, ambiguous, and likely to drift into unsupported shortcuts

### Option 2: Put Guidance Only In README

- Pros: visible to humans
- Cons: too broad, not explicit enough for agent operating rules

### Option 3: Maintain A Dedicated Skill And Guide

- Pros: explicit command order, provenance rules, agent-focused wording
- Cons: another documentation artifact to maintain

## Decision

Maintain explicit agent guidance through a dedicated skill document and an analyst/agent guide, with the canonical command order:

`fetch` or `submit` -> `normalize` -> `research` -> `ingest` -> `rank` -> `explain`

## Consequences

### Positive

- agents have a clear operating contract
- provenance guardrails are easier to preserve
- workflow drift becomes easier to detect in review

### Negative

- documentation and code must stay aligned
- future command surface changes require doc updates as part of normal development

## Related Documents

- `skills/signal-graph/SKILL.md`
- `docs/runbooks/analyst-agent-guide.md`
