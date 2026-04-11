# Deep Interview Spec — signal-graph-agent-signal-journal

## Metadata

- Date: 2026-04-11
- Profile: deep
- Mode flags: autoresearch
- Final ambiguity: 13%
- Threshold: 15%
- Context type: brownfield
- Official product name: Signal Graph
- Context snapshot: `.omx/context/sigma-graph-intent-signals-20260411T153520Z.md`
- Transcript: `.omx/interviews/signal-graph-agent-signal-journal-20260411T160342Z.md`

## Clarity Breakdown

| Dimension | Score |
| --- | ---: |
| Intent | 0.84 |
| Outcome | 0.82 |
| Scope | 0.84 |
| Constraints | 0.72 |
| Success | 0.86 |
| Context | 0.88 |

Readiness gates:
- Non-goals: resolved
- Decision boundaries: resolved
- Pressure pass: complete

## Intent

Evolve Signal Graph from a trading-event provenance toolkit into a broader **agent signal memory and decision-support substrate** that captures signals without quality loss, preserves provenance, supports recall/query/interpretation, and remains deterministic and agent-operable.

## Desired Outcome

## Canonical Product Framing

## PRD-Ready Product Principles

1. **Lossless by default**
   Signal Graph preserves raw signal fidelity or a durable raw-reference before producing summaries, interpretations, or recall artifacts.

2. **Provenance is part of the product, not metadata exhaust**
   Every important artifact should explain what source signal it came from, who or what produced it, and how it was derived.

3. **Do not invent `why`**
   Signal Graph records `why` only when intention is explicit, well-supported, or clearly marked as inference.

4. **User and agent actions belong in the same memory system**
   Signal Graph must capture both what users did and what agents did on their behalf, with enough identity context to distinguish them.

5. **Graph structure must improve recall, not decorate it**
   `who / what / when / where / why / how` should act as retrieval pivots and explanation paths, not just descriptive labels.

6. **Deterministic over magical**
   The system should prefer reproducible, inspectable behavior over opaque automation that cannot be audited.

7. **CLI-first, MCP-ready**
   The core recall and summarization workflow must work well from the CLI and be cleanly exposable through an MCP server surface.

8. **Artifacts must be agent-usable and human-readable**
   Outputs should be easy for agents to consume programmatically and easy for humans to inspect in markdown or file-backed form.

9. **Tight scope before broad coverage**
   Signal Graph should prove the journal and recall loop before expanding connector breadth, UI surface, or autonomous research behavior.

10. **Every action can become a new signal**
   The system should support a compounding loop where interpreted signals lead to actions, and those actions generate new signals that re-enter the graph with provenance.

### Product vision paragraph
Signal Graph is the lossless memory and provenance engine for users and AI agents. It remembers what happened, who did it, what it was about, when and where it occurred, and only records why when intent is genuinely clear or explicitly marked as inference. It turns those signals into traceable, queryable, graph-linked artifacts that can be accessed through the CLI and MCP, then reused by downstream signal interpreters to recommend next actions and generate new signals in a compounding feedback loop.

### JTBD
When I or my AI agents do meaningful work, I want Signal Graph to reliably capture and preserve those signals with provenance, so I can later query, summarize, and act on them without losing context, trust, or quality.

### Success metrics
#### Core product metrics
- **Signal capture coverage:** at least 5 end-to-end signals captured across multiple sessions in the v1 proof.
- **Provenance completeness:** 100% of recall artifacts in the v1 proof trace back to source signal, origin metadata, and graph/file reference.
- **Losslessness:** 100% of v1 proof artifacts preserve raw content or durable raw-reference recoverability.
- **Determinism:** repeated runs on the same inputs produce materially identical artifacts and recall paths.
- **Recall usability:** CLI recall succeeds across all v1 proof signals with explicit provenance output.

#### Product-fit metrics for later stages
- **Agent-action coverage:** users can inspect both user-originated and agent-originated signals in the same recall surface.
- **MCP usefulness:** the same recall/summarization surfaces exposed by CLI are consumable through MCP without changing the trust model.
- **Interpreter loop readiness:** at least one downstream interpreter can consume Signal Graph outputs and emit a new signal that is re-captured with provenance.

### Anti-goal / failure statement
If Signal Graph cannot tell a user what happened, who/what produced it, where it came from, and how the current recall artifact was derived — while preserving the raw signal without summary-only collapse — then it has not achieved the intended product outcome.

## User-Articulated Success Outcome

The user's desired future user sentiment is effectively:

- Signal Graph remembers what the user did and what AI agents did on the user's behalf
- It preserves **who, what, when, where**, and **why only when intention is genuinely clear**
- Those signals can later be queried and summarized through the **CLI** and as an **MCP server surface**
- Those signals become inputs to downstream **signal interpreters** that recommend next actions
- The recommended/next actions themselves generate new signals that feed back into Signal Graph

Implications:
- Signal Graph should avoid fabricating `why`; inferred intent must be explicit and provenance-bound
- MCP access should be treated as a real product surface, not just a future nice-to-have
- The longer-term architecture should include a closed-loop pattern: **capture -> recall/query -> interpret -> act -> emit new signals -> recapture**

Signal Graph should become the strongest local-first, provenance-first system in its class for:
- capturing raw signals from users, agents, and references
- preserving traceability from recall artifacts back to original signals
- structuring signal paths through who / what / when / where / why / how
- producing agent-friendly markdown artifacts for recall and downstream work
- supporting a staged roadmap from journal → recall/query → self-install/integration

## In-Scope

### v1 milestone: Agent signal journal
Build the first end-to-end capability around:
1. capturing a raw signal from an agent/user/reference flow
2. attaching agent identity metadata (host, process, session id, role)
3. preserving verbatim/raw content or raw reference pointer without collapse into summary-only storage
4. generating a markdown recall artifact with explicit provenance sections
5. writing graph links across who / what / when / where / why / how
6. supporting at least one provenance-rich recall path back to source

### Later stages already accepted by user
2. high-quality recall/query engine
3. agent self-install/setup/integration workflows

## Out-of-Scope / Non-goals for v1

- Broad connector coverage
- Autonomous research / web discovery
- Dashboard / rich UI

## Decision Boundaries

Locked boundary: **Option 4**

OMX may decide without further approval:
- exact schema design
- CLI command names
- markdown artifact format
- graph edge and path model

User approval is still required for:
- branding / repositioning changes
- major scope expansion beyond the v1 agent signal journal

## Constraints

- Preserve the official product name: **Signal Graph**
- Stay brownfield-aware; extend the existing CLI-first, provenance-aware, SQLite + Neo4j + filesystem architecture rather than discarding it
- Keep the first cut local, deterministic, auditable, and replayable
- Preserve provenance discipline already present in the repo: separation of fact, graph implication, and inference
- Compete on depth and traceability rather than connector breadth

## Testable Acceptance Criteria

### Primary non-negotiable tests
1. **Provenance traceability**: every recall artifact in v1 must be traceable back to source signals, actor/session identity, and graph path / file reference.
2. **Losslessness**: v1 must not rely on summary-only storage; raw signal fidelity or raw-signal reference must remain recoverable.

### Measurable proof threshold selected by user
- **Option C — Higher bar**
- At least **5 signals** captured end-to-end across **multiple sessions**
- Signals should cover the accepted v1 origin types where feasible (user, agent artifact, external/reference)
- A recall/query flow must be tested across those signals
- Provenance traceability, losslessness, and determinism must be demonstrated repeatedly, not just once

### Important secondary tests
- Determinism: same inputs should yield stable artifacts/paths
- Agent usability: an agent should be able to write and retrieve signals through a clear workflow
- Recall quality: recall should be better than flat notes/keyword-only lookup
- Signal topology: who/what/when/where/why/how must materially improve navigation and recall

## Assumptions Exposed + Resolutions

- **Assumption:** competitive advantage could come from doing everything at once.
  - **Resolution:** user accepted staged sequencing instead of simultaneous breadth.
- **Assumption:** Signal Graph might need a renamed identity.
  - **Resolution:** user explicitly kept the official name as Signal Graph.
- **Assumption:** all success criteria could be equally primary.
  - **Resolution:** user chose provenance traceability and losslessness as the two non-negotiables.

## Pressure-pass Findings

The most important revisited answer was the success bar. The user first accepted a broad set of desirable criteria, but when forced to trade off, chose **provenance traceability** and **losslessness** as the defining bar. This materially changed the center of gravity of the spec from “general memory” toward “lossless signal provenance.”

## Brownfield Evidence vs Inference Notes

### Repo-grounded evidence
- `src/signal_graph/services/explain.py` already emits markdown memo artifacts and separates fact, graph implication, and inference.
- `src/signal_graph/models/source.py`, `events.py`, `research.py`, and `storage/schema.sql` already model raw items, event candidates, research bundles, and graph events.
- `docs/architecture/system-overview.md` and ADRs show a CLI-first, provenance-aware, SQLite + Neo4j split.

### Inferences for future design
- The current models appear to lack first-class agent host/process/session identity.
- The current graph model appears not yet to encode who/what/when/where/why/how as explicit recall topology.
- The current system appears stronger in event provenance than in general signal journaling and recall.

## Technical Context Findings

Likely brownfield touchpoints for later planning:
- `src/signal_graph/models/source.py`
- `src/signal_graph/models/events.py`
- `src/signal_graph/models/research.py`
- `src/signal_graph/storage/schema.sql`
- `src/signal_graph/services/raw_items.py`
- `src/signal_graph/services/explain.py`
- `src/signal_graph/graph/schema.py`
- `docs/architecture/system-overview.md`
- `docs/runbooks/analyst-agent-guide.md`

## Mission Draft

See: `.omx/specs/autoresearch-signal-graph-agent-signal-journal/mission.md`

## Evaluator Draft

See: `.omx/specs/autoresearch-signal-graph-agent-signal-journal/result.json` field `evaluatorCommand`.

## Launch Readiness

- Status: **launch-ready draft**
- Reason: the user explicitly chose launch-ready draft mode and the evaluator command contains no placeholder markers.

## Seed Inputs

- Inspirations:
  - GBrain — https://github.com/garrytan/gbrain
  - MemPalace — https://github.com/milla-jovovich/mempalace
  - GitHubAwesome trend roundup dated **December 14, 2025** — https://githubawesome.com/25-ai-agent-projects-julep-big-agi-anytool-playwriter-vibe-kanban-agent-s-potpie-liveblocks/
- Strategic thesis:
  - Signal Graph should compete as a deterministic, provenance-first, lossless signal memory and decision-support system for agents.

## Confirmation Bridge

After this deep interview, the appropriate next actions are:
- **refine further** if you want tighter measurable thresholds or more competitive analysis
- **launch** if you want the autoresearch mission executed next
- **$ralplan** if you want architecture and test-shape planning directly from this clarified brief

## Recommended Handoff

Recommended next step: **`$ralplan`** using this spec as the requirements source of truth.

Alternative if you want market/depth research first: use the autoresearch bundle in `.omx/specs/autoresearch-signal-graph-agent-signal-journal` and explicitly choose **launch** in the next turn.
