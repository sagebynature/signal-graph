# Product Overview

## Summary

`Signal Graph` V2 is a local, CLI-first **memory and decision-support system** for humans and AI tools.

Its job is to preserve owner-scoped facts, actions, artifacts, and corrections with enough provenance to later answer: **what happened, who did it, what evidence existed, and why was a choice made?**

The current repository still carries a brownfield V1 trading-research workflow, but that is now treated as a superseded legacy lane inside the rewrite workspace.

## The Problem It Solves

People increasingly work across multiple AI tools, machines, and shared artifacts. The hard part is not generating another answer; it is preserving trustworthy context that survives handoffs and can be corrected later.

Common failure modes:

- the same action appears in several noisy forms across tools or devices
- shared files lose provenance once they are summarized downstream
- inferred intent is stored as fact without confidence labeling
- later explanations cannot show which owner, actor, or artifact drove a decision
- corrective feedback such as “don’t do that again” is not persisted in a deterministic way

Signal Graph V2 is designed to sit between raw AI/tool activity and later retrieval or explanation. It forces the memory chain into visible stages.

## Product Shape

Signal Graph V2 is best understood as a memory loop:

`owner + actor identity -> hook/share capture -> append-only events + canonical raw artifacts -> graph/index projections -> retrieval/explanation -> correction/redaction`

That workflow is implemented as explicit CLI and MCP surfaces, local state, and inspectable artifacts so humans and coding agents can operate it the same way.

## Who It Is For

- A human operator who wants a durable memory layer across AI tools and devices
- A team using coding agents that need owner-scoped recall and explainable provenance
- A developer building local memory capture, explanation, or correction workflows
- A stakeholder evaluating whether the V2 product shape is coherent, bounded, and extensible

## Primary Use Cases

### Hook-Driven Memory Capture

A human works through Codex, Claude Code, Gemini, or another supported tool and wants pre-action and post-output events captured with explicit owner, actor, and session provenance.

### Shared Artifact Recall

A user shares a document or folder and later needs the system to retrieve the share event, raw artifact evidence, and derived interpretations without mutating source truth.

### Explanation Of Prior Decisions

Later, the user asks why a specific approach was chosen. The system returns an explanation shape that links owner, actor, action/decision, provenance chain, evidence refs, and confidence-labeled `why` when present.

### Correction And Redaction

The user says “don’t do that in the future” or requests removal/redaction. The system records a first-class correction artifact and exposes deterministic downstream effects in follow-up retrieval or explanation results.

## What Makes It Different

- Owner-scoped memory instead of anonymous transcript dumping
- Provenance-aware capture instead of summary-first recall
- Explicit correction/redaction semantics instead of ad hoc prompt tweaking
- CLI/MCP-native operation instead of hidden UI-only state

## Current Maturity

This repository is an active rewrite workspace. The accepted V2 product decisions are now documented, but implementation is still split between:

- brownfield V1 runtime surfaces that remain operational
- journal and MCP capabilities that already preserve some provenance-rich recall
- planned V2 domain/storage/transport work that is still being built inside this repo

## What This Cut Does Not Try To Do

- Replace human judgment with opaque autonomous decisions
- Offer a hardened public multi-tenant HTTP product in the MVP
- Treat inferred preferences as facts without confirmation
- Erase or overwrite raw evidence when derived interpretations change
- Keep the V1 trading-research proposition as the primary product story for V2

## Read Next

- Landing page: [`../../README.md`](../../README.md)
- Architecture: [`../architecture/system-overview.md`](../architecture/system-overview.md)
- Local operation: [`../runbooks/operator-guide.md`](../runbooks/operator-guide.md)
- Brownfield workflow: [`../runbooks/analyst-agent-guide.md`](../runbooks/analyst-agent-guide.md)
