# ADR-0003: Encode Agent Usage Through Bootstrap And Journal Workflow Contracts

## Status
Accepted

## Context

The repository is operated by humans and coding agents. Agents need more than API access; they need a safe workflow contract that says where runtime guidance lives, which commands are supported, and which artifacts prove the system is working.

## Decision Drivers

- keep runtime instructions aligned with the supported CLI
- make bootstrap and automation discovery explicit
- preserve provenance guardrails for capture, journaling, and recall

## Considered Options

### Option 1: Let agents infer workflow from source code
Rejected because command discovery and runtime contracts become inconsistent.

### Option 2: Put guidance only in README
Rejected because bootstrap, automation, and MCP details drift too easily.

### Option 3: Maintain a dedicated skill and guide
Accepted because the skill, README, and operator guide can point to the same supported surfaces.

## Decision

Signal Graph documents and skill guidance will standardize on this order:

`doctor -> init -> bootstrap-describe / automation-describe -> capture-signal -> journalize-signal -> recall-signal -> mcp-server`

The skill file and operator docs should reinforce supported runtime contracts rather than historical workflows.

## Consequences

### Positive
- agents have a clear operating contract
- bootstrap and automation guidance stay aligned with CLI help
- workflow drift becomes easier to detect in review

### Negative
- documentation updates must stay coordinated across README, runbooks, and skill text

## Related Documents

- `../../skills/signal-graph/SKILL.md`
- `../runbooks/operator-guide.md`
- `../architecture/system-overview.md`
