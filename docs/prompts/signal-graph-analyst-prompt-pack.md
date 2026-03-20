# Signal Graph Analyst Prompt Pack

This playbook is for non-technical analysts using `Signal Graph` as a structured research workflow rather than a coding surface.

Core operating model:

`raw event -> normalized event candidate -> researched bundle -> graph event -> ranked candidates -> memo`

This document complements:

- `docs/runbooks/analyst-agent-guide.md`
- `docs/overview/product.md`
- `docs/architecture/system-overview.md`

## What This Pack Is For

Use this pack when you want to turn a messy market event into a repeatable chain of:

- captured source material
- structured event framing
- evidence and contradictions
- graph-based spillover reasoning
- ranked expressions
- memo output

The output is decision-support research. It is not trading advice.

## Current Scope Note

In practice, Signal Graph works best when the event has:

- one clear primary entity
- a clear positive or negative direction
- a plausible spillover path to related companies, ETFs, suppliers, customers, or themes
- enough public evidence to support both a thesis and any contradictions

## Prompt Pack

### 1. Rapid Triage

Use when: you have one headline or event note and need a fast first-pass view of what matters.

```text
Use Signal Graph to analyze this market event quickly but rigorously. Capture the event, structure it into a clean event record, attach supporting research and at least one counterpoint, then rank the most relevant stocks or ETFs and produce a short memo. In the final output, clearly separate confirmed facts, graph-based implications, and your own inference. Present the result as research support, not trading advice.

== Event ==
[insert event]
```

### 2. Spillover Map

Use when: the first-order reaction is obvious, but you want to find second-order names or thematic exposures.

```text
Use Signal Graph to map the full market spillover from this event. I do not want only the obvious direct exposure. Show me the direct company impact, related ETFs, and any second-order supplier, customer, or ecosystem effects that appear in the graph reasoning. Explain why each candidate appears and what relationship path supports it.

== Event ==
[insert event]
```

### 3. Breaking News Review

Use when: you want a more rigorous version of headline triage with explicit uncertainty handling.

```text
Use Signal Graph to treat this as breaking-news triage. Turn the headline into a structured event, attach evidence, include any contradictions or uncertainty, then rank the most relevant expressions and generate a memo. I want a decision-support summary that tells me what is known, what the graph suggests, and what remains uncertain.

== Event ==
[insert event]
```

### 4. Bull vs Bear Case

Use when: the event is contested, ambiguous, or likely to produce overconfident storytelling.

```text
Use Signal Graph to evaluate both sides of this event hypothesis. Build the research record with supporting evidence and contradictory evidence, then continue through ranking and memo generation. The final output should preserve both the bullish and bearish interpretation instead of collapsing everything into a single conclusion.

== Event ==
[insert event]
```

### 5. Compare Two Narratives

Use when: you want to understand how different event types create different market read-throughs.

```text
Use Signal Graph to compare these two event hypotheses side by side. Run each through the full workflow and compare the ranked candidates, timing windows, and memo narratives. Make it easy to see how different event types produce different market read-throughs, while keeping facts separate from implications and inference.

== Event A ==
[insert event A]

== Event B ==
[insert event B]
```

### 6. ETF Read-Through

Use when: you care more about sector or thematic expression than single-name exposure.

```text
Use Signal Graph to identify the best ETF-based expression of this event. I want the output to focus on sector or thematic ETF exposure rather than only single-name equities. Show which ETFs rank highest, why they rank, what graph path supports them, and whether the likely reaction window is immediate or short-drift.

== Event ==
[insert event]
```

### 7. Existing Research Replay

Use when: you want to reuse local work instead of starting a fresh research cycle.

```text
Use Signal Graph to work only from the research that is already stored locally. Find the most recent relevant event, review its evidence and graph relationships, rerun ranking if needed, and generate a fresh memo for the strongest candidate. Do not fetch new information unless local state is missing. Tell me exactly what stored research the conclusion relies on.
```

### 8. Weak Signal Diagnosis

Use when: the output looks thin, unconvincing, or strangely empty and you want a root-cause explanation.

```text
Use Signal Graph to investigate why the output for this event looks weak, sparse, or unconvincing. Check whether the event was structured clearly enough, whether the key entity is recognized in the graph, and whether local policy settings may be affecting the result. If you identify the problem, fix it and rerun the workflow. Explain the root cause in plain English.

== Event ==
[insert event]
```

### 9. Policy Sensitivity Check

Use when: you want to understand how much the ranking depends on local scoring assumptions.

```text
Use Signal Graph to show how local scoring policy changes the interpretation of this event: "[insert event]." Review the current local scoring settings, adjust them for this type of event, rerun the ranking, and compare the before-and-after results. Be explicit about which differences come from local policy choices rather than from new evidence.
```

### 10. Provenance Audit

Use when: you need to verify that the research chain is complete and internally consistent.

```text
Use Signal Graph to audit the full research chain for this event. Verify that the original source item, structured event, research bundle, graph event, ranked candidates, and final memo all exist and connect properly. If any stage is missing or inconsistent, stop and explain exactly where the chain breaks.

== Event ==
[insert event]
```

### 11. Executive Summary Memo

Use when: you want the output condensed into something a PM, portfolio manager, or research lead can scan quickly.

```text
Use Signal Graph to produce an executive-ready memo for this event: "[insert event]." Run the full workflow, then write a concise final summary that highlights the event, strongest candidate expressions, main supporting evidence, key contradictions, likely timing window, and remaining uncertainty. Keep the tone analytical and decision-support oriented.
```

## Best Event Types For Signal Graph

Signal Graph is strongest when the event can be structured cleanly and has believable spillover paths. Good fits include:

- regulatory actions affecting a named company or industry
- export restrictions, sanctions, or tariff changes
- production cuts, capacity additions, or capex changes
- plant outages, labor strikes, or supply disruptions
- product recalls or major operational failures
- mergers, divestitures, and strategic partnerships
- clinical-trial updates or FDA actions
- pricing actions with likely supplier, customer, or ETF read-through
- commodity shocks linked to a specific producer, geography, or downstream industry
- large customer wins or losses with ecosystem implications

Signal Graph is usually weaker when the event is too broad or too detached from identifiable entities and relationships, such as:

- generic macro commentary with no obvious primary entity
- loose thematic claims with little source evidence
- pure valuation arguments without an event trigger
- sentiment-only narratives that do not map to a concrete event

## Filled-In Industry Examples

These examples are useful prompt templates for analysts, even if the current local graph universe may need extension before they produce strong end-to-end ranking output.

### Example 1. Energy Shock

Best for: rapid triage, spillover mapping, ETF read-through

```text
Use Signal Graph to analyze this market event quickly but rigorously: "OPEC announces deeper oil production cuts." Capture the event, structure it into a clean event record, attach supporting research and at least one counterpoint, then rank the most relevant stocks or ETFs and produce a short memo. In the final output, clearly separate confirmed facts, graph-based implications, and your own inference. Present the result as research support, not trading advice.
```

### Example 2. Biotech Regulatory Risk

Best for: breaking-news review, bull vs bear case

```text
Use Signal Graph to treat this as breaking-news triage: "The FDA places a clinical hold on a mid-stage biotech trial." Turn the headline into a structured event, attach evidence, include any contradictions or uncertainty, then rank the most relevant expressions and generate a memo. I want a decision-support summary that tells me what is known, what the graph suggests, and what remains uncertain.
```

### Example 3. Airline Operations Disruption

Best for: spillover mapping, compare two narratives

```text
Use Signal Graph to map the full market spillover from this event: "A major airline grounds part of its fleet after an engine inspection directive." I do not want only the obvious direct exposure. Show me the direct company impact, related ETFs, and any second-order supplier, customer, or ecosystem effects that appear in the graph reasoning. Explain why each candidate appears and what relationship path supports it.
```

### Example 4. Mining Supply Disruption

Best for: rapid triage, weak signal diagnosis

```text
Use Signal Graph to analyze this market event quickly but rigorously: "A labor strike shuts down a major copper mine in Chile." Capture the event, structure it into a clean event record, attach supporting research and at least one counterpoint, then rank the most relevant stocks or ETFs and produce a short memo. In the final output, clearly separate confirmed facts, graph-based implications, and your own inference. Present the result as research support, not trading advice.
```

### Example 5. Payments Regulation

Best for: policy sensitivity check, executive summary memo

```text
Use Signal Graph to show how local scoring policy changes the interpretation of this event: "A regulator proposes tighter interchange fee caps for major card networks." Review the current local scoring settings, adjust them for this type of event, rerun the ranking, and compare the before-and-after results. Be explicit about which differences come from local policy choices rather than from new evidence.
```

### Example 6. Consumer Health Retail Restructuring

Best for: executive summary memo, provenance audit

```text
Use Signal Graph to produce an executive-ready memo for this event: "A national pharmacy chain announces a large wave of store closures." Run the full workflow, then write a concise final summary that highlights the event, strongest candidate expressions, main supporting evidence, key contradictions, likely timing window, and remaining uncertainty. Keep the tone analytical and decision-support oriented.
```

## How To Choose Quickly

If you only remember three options:

- use `Rapid Triage` for first-pass event review
- use `Spillover Map` when you want second-order names and ETFs
- use `Provenance Audit` when you need to trust the chain before trusting the conclusion
