# Signal Graph Analyst Prompt Pack

This pack is for non-technical analysts using `Signal Graph` as a structured research workflow rather than a coding surface.

Core operating model:

`raw event -> normalized event candidate -> researched bundle -> graph event -> ranked candidates -> memo`

This document complements:

- `docs/runbooks/analyst-agent-guide.md`
- `docs/overview/product.md`
- `docs/architecture/system-overview.md`

## What This Pack Is For

Use this pack when you want to turn a messy market event into a repeatable chain of:

- source capture
- structured event framing
- supporting evidence and contradictions
- graph-based spillover reasoning
- ranked expressions
- memo output

The output is decision-support research. It is not trading advice.

## Best Fit

Signal Graph is strongest when the event has:

- one clear primary entity
- a clear positive or negative direction
- a plausible spillover path to related companies or ETFs
- enough public evidence to support both a thesis and at least one counterpoint

Assume the operator may be starting from a fresh local graph with little or no prior state. The prompt should therefore make the event framing, evidence needs, and desired output explicit instead of assuming relevant entities or relationships already exist locally.

## How To Use This Pack

1. Start with the `Base Analyst Prompt`.
2. Add one task module from `Prompt Library`.
3. Replace the bracketed fields.
4. If the output is thin or confusing, run `Weak Signal Diagnosis` or `Provenance Audit`.

## Base Analyst Prompt

Use this base block for every workflow. It makes the prompt pack more consistent and keeps the output aligned with the actual CLI pipeline.

```text
Use Signal Graph as a provenance-aware research workflow, not as a chat-style summary tool.

Work in this order:
1. Capture or locate the source item for the event.
2. Normalize it into a clean event candidate.
3. Attach supporting evidence, contradictions, and confidence context.
4. Ingest the researched event for graph reasoning.
5. Rank the most relevant candidate expressions.
6. Produce a memo.

Operating rules:
- Prefer already stored local state before fetching new information.
- If local scoring policy is active, say so explicitly because it can change rank order, timing windows, and memo wording.
- Never blur confirmed fact, graph implication, and your own inference.
- Treat contradictions as part of the record, not as noise to hide.
- Present the result as decision-support research, not trading advice.

Return the final answer in this structure:

## Event Record
- Event summary
- Primary entity
- Event type
- Direction
- What is confirmed
- What is assumed or unresolved

## Evidence And Contradictions
- Supporting evidence with provenance
- Contradictory evidence or uncertainty
- Research confidence

## Ranked Candidates
For each candidate include:
- ticker
- company or ETF name
- score or relative rank
- timing window
- matched entity
- relationship path
- short reason summary

## Memo
Write a concise memo that clearly separates:
- Confirmed Facts
- Graph Implications
- Analyst Inference

== Event ==
[insert event]

== Preferences ==
Asset universe: [single names | ETFs | both]
Memo length: [short | standard | executive]
Fetch policy: [local first | allow web if needed]
```

## Prompt Library

Each module below is designed to be appended after the `Base Analyst Prompt`.

### 1. Rapid Triage

Use when: you have one headline or event note and need a fast first pass.

```text
Priority: speed with discipline.

Focus on:
- the cleanest event framing
- the most relevant evidence
- at least one serious counterpoint
- the top 3 candidate expressions

Keep the memo short and decision-oriented.
```

### 2. Spillover Map

Use when: the first-order reaction is obvious, but you want second-order names or ETF exposure.

```text
Priority: propagation logic.

Do not stop at the obvious direct exposure. Show:
- direct company impact
- related ETFs
- second-order supplier, customer, peer, or ecosystem effects

For each ranked candidate, explain the relationship path that makes it relevant.
```

### 3. Breaking News Review

Use when: the event is fresh and you need explicit uncertainty handling.

```text
Priority: what is known now versus what still needs confirmation.

Be strict about uncertainty:
- identify what is actually confirmed
- identify what comes from early or incomplete reporting
- include at least one contradiction or missing-data warning

If the event is too underdeveloped for strong ranking, say so plainly.
```

### 4. Bull vs Bear Case

Use when: the event is contested, ambiguous, or likely to attract overconfident storytelling.

```text
Priority: preserve both sides of the case.

Build the research record so the final memo includes:
- the strongest bull interpretation
- the strongest bear interpretation
- which ranked candidates benefit under each interpretation

Do not collapse the final answer into one forced conclusion if the evidence is mixed.
```

### 5. Compare Two Narratives

Use when: you want to compare two possible event framings or two competing reads of the same situation.

```text
Run the workflow separately for both narratives, then compare them side by side.

For the comparison, show:
- differences in event framing
- differences in supporting evidence and contradictions
- differences in ranked candidates
- differences in likely timing windows

Make it easy to see whether the ranking changed because the narrative changed or because the evidence quality changed.

== Event A ==
[insert event A]

== Event B ==
[insert event B]
```

### 6. ETF Read-Through

Use when: you care more about sector or thematic expression than single-name exposure.

```text
Priority: ETF expression over individual equities.

Rank ETFs first. If single names appear, use them only as supporting context.

For each ETF candidate, explain:
- why it ranks
- which entities or themes drive the exposure
- whether the likely reaction window is immediate, short-drift, or slower-developing
```

### 7. Existing Research Replay

Use when: you want to reuse stored local work instead of starting a fresh research cycle.

```text
Work from local stored state first.

Find the most recent relevant event, review its evidence and graph relationships, rerun ranking if needed, and generate a fresh memo for the strongest candidate.

Do not fetch new information unless local state is missing or clearly stale.

Tell me exactly which stored artifacts the final conclusion relies on.
```

### 8. Weak Signal Diagnosis

Use when: the output looks thin, unconvincing, or oddly empty.

```text
Treat this as a root-cause diagnosis.

Check:
- whether the event was framed clearly enough
- whether the primary entity resolves cleanly
- whether evidence and contradictions were actually attached
- whether graph coverage is too weak for this entity or theme
- whether local scoring policy is affecting the result

If you identify the problem, fix what you can and rerun the workflow.

Explain the root cause in plain English before giving the rerun result.
```

### 9. Policy Sensitivity Check

Use when: you want to see how much the ranking depends on local scoring assumptions.

```text
Treat this as a before-versus-after comparison.

Review the active local scoring policy, adjust it for this event type, rerun ranking, and compare the results.

Be explicit about:
- which settings changed
- which candidates moved
- whether timing windows changed
- which differences come from policy rather than new evidence
```

### 10. Provenance Audit

Use when: you need to verify that the research chain is complete and internally consistent.

```text
Audit the full workflow chain for this event.

Verify that all of these exist and connect properly:
- original source item
- normalized event candidate
- research bundle
- graph event
- ranked candidates
- final memo artifact

If any stage is missing, inconsistent, or unsupported by stored provenance, stop and explain exactly where the chain breaks.
```

### 11. Executive Summary Memo

Use when: you want the output condensed for a PM, portfolio manager, or research lead.

```text
Priority: scanability for a senior reader.

Run the full workflow, then end with an executive-ready memo that highlights:
- the event
- strongest candidate expressions
- main supporting evidence
- key contradictions
- likely timing window
- remaining uncertainty

Keep the tone analytical and concise.
```

## Best Event Types For Signal Graph

Signal Graph is strongest when the event can be structured cleanly and has believable spillover paths. Good fits include:

- export restrictions or sanctions affecting a named company or supply chain
- capex cuts or capacity expansions
- plant outages, labor actions, or supply disruptions
- pricing changes with supplier, customer, or ETF read-through
- product delays, shipment constraints, or operational failures
- large customer wins or losses with ecosystem implications
- regulatory actions tied to a specific company or subsector

Signal Graph is usually weaker when the event is too broad or too detached from identifiable entities and relationships, such as:

- generic macro commentary with no obvious primary entity
- loose thematic claims with little source evidence
- pure valuation arguments without an event trigger
- sentiment-only narratives that do not map to a concrete event

## Copy-Paste Full Prompt Examples

These examples are written as realistic copy-paste starting points. They do not assume that a particular graph universe is already preloaded.

### Example 1. TSMC Capex Cut

Best for: `Rapid Triage`, `Spillover Map`

```text
Use Signal Graph as a provenance-aware research workflow, not as a chat-style summary tool.

Work in this order:
1. Capture or locate the source item for the event.
2. Normalize it into a clean event candidate.
3. Attach supporting evidence, contradictions, and confidence context.
4. Ingest the researched event for graph reasoning.
5. Rank the most relevant candidate expressions.
6. Produce a memo.

Operating rules:
- Prefer already stored local state before fetching new information.
- Never blur confirmed fact, graph implication, and your own inference.
- Treat contradictions as part of the record, not as noise to hide.
- Present the result as decision-support research, not trading advice.

Focus on a fast first pass with the top 3 candidate expressions.

== Event ==
TSMC signals a meaningful capex reduction for the next planning cycle because end-market demand remains weaker than expected.

== Preferences ==
Asset universe: both
Memo length: short
Fetch policy: local first
```

### Example 2. NVDA Export Restriction Review

Best for: `Breaking News Review`, `Bull vs Bear Case`

```text
Use Signal Graph as a provenance-aware research workflow, not as a chat-style summary tool.

Run the event through source capture, normalization, research, ingest, ranking, and memo generation.

Be strict about uncertainty:
- identify what is confirmed
- identify what still comes from incomplete reporting
- include both the strongest bull and bear interpretation

In the final memo, separate Confirmed Facts, Graph Implications, and Analyst Inference.

== Event ==
U.S. authorities appear to be expanding AI chip export controls in ways that could further constrain NVDA shipments into China.

== Preferences ==
Asset universe: both
Memo length: standard
Fetch policy: allow web if needed
```

### Example 3. ASML Shipment Delay ETF Read-Through

Best for: `ETF Read-Through`

```text
Use Signal Graph as a provenance-aware research workflow, not as a chat-style summary tool.

Rank ETFs first and use single names only as supporting context.

For each ETF candidate, explain:
- why it ranks
- which entities or themes drive the exposure
- whether the likely reaction window is immediate, short-drift, or slower-developing

In the final memo, separate Confirmed Facts, Graph Implications, and Analyst Inference.

== Event ==
ASML reports a meaningful shipment delay for advanced lithography systems, creating concern about downstream semiconductor equipment timing.

== Preferences ==
Asset universe: ETFs
Memo length: standard
Fetch policy: local first
```

### Example 4. Intel Delay Provenance Audit

Best for: `Provenance Audit`, `Weak Signal Diagnosis`

```text
Use Signal Graph to audit and, if needed, diagnose the workflow output for this event.

Verify that all of these exist and connect properly:
- original source item
- normalized event candidate
- research bundle
- graph event
- ranked candidates
- final memo artifact

If the chain is weak, explain whether the problem comes from event framing, entity resolution, missing evidence, graph coverage, or local scoring policy. Fix what you can and rerun the workflow.

== Event ==
Intel appears to be delaying a key foundry milestone, raising questions about spillover to peers and semiconductor ETFs.

== Preferences ==
Asset universe: both
Memo length: short
Fetch policy: local first
```

## How To Choose Quickly

If you only remember four options:

- use `Rapid Triage` for first-pass event review
- use `Spillover Map` when you want second-order names and ETFs
- use `Weak Signal Diagnosis` when the result looks suspiciously thin
- use `Provenance Audit` when you need to trust the chain before trusting the conclusion
