# Competitive Assessment

Signal Graph is well-positioned to compete if it leans into a lane that adjacent systems only partially cover: **lossless signal capture with deterministic provenance and graph-backed recall**.

## What the current market finds appealing

1. **Raw retention over summary-only memory**  
   MemPalace's public framing emphasizes storing raw/verbatim exchanges and making them findable later, rather than trusting an LLM to decide what matters up front. That directly matches the user's thesis that signal quality must not collapse during capture.

2. **Agent-operable installation and rituals**  
   GBrain's README makes the agent the installer/operator, not just the end-user. That matters because agent adoption is accelerated when the system ships with explicit setup, ingestion, and upkeep playbooks.

3. **Markdown or file-native source of truth**  
   GBrain's markdown-first model is appealing because humans can inspect and edit it directly. Signal Graph already has a filesystem artifact boundary and can extend that without abandoning its SQLite + Neo4j split.

4. **Structured recall, not just flat search**  
   MemPalace's “wings / halls / rooms” framing and the broader GitHubAwesome trend coverage suggest users want navigable memory topology, not merely embeddings plus keyword search.

5. **Operational trust**  
   Signal Graph already has an advantage here: the repo separates fact, graph implication, and inference, and explicitly treats provenance as a first-class concern. That is a stronger trust posture than generic “memory layer” products.

## Where Signal Graph can be meaningfully differentiated

### 1. Provenance-first memory instead of generic memory
Signal Graph should position itself as the system that answers: **what was the original signal, who/what produced it, when, why does this recall exist, and how did the system derive this artifact?**

### 2. Lossless-first capture instead of compression-first memory
Signal Graph should preserve raw signal text, payloads, or durable references to them before any summarization. Summaries are derivative artifacts, not the primary memory substrate.

### 3. Signal topology instead of flat memory buckets
The who / what / when / where / why / how frame should become an explicit signal graph topology for ingestion, linking, and recall. This should be more than tags; it should define graphable relationships and retrieval pivots.

### 4. Agent identity as a core part of provenance
Signals originating from an agent should carry host, process, runtime, session id, role, and derivation lineage so later recall can distinguish user-originated signals from agent-created artifacts and external references.

### 5. Deterministic artifacts over opaque “smart memory” behavior
Signal Graph should make outputs reproducible and inspectable. The current repo already values deterministic local behavior and explicit workflow ordering; this should remain a core product trait.

# Recommended v1 Scope

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

## Recommended v1 milestone: Agent signal journal

The first milestone should prove one end-to-end capability:

1. capture raw signals from at least these origin types where feasible:
   - direct user signal
   - agent action artifact
   - external/reference signal
2. persist signal records with origin metadata and agent/session identity
3. preserve raw fidelity or raw-reference recoverability
4. emit agent-friendly markdown recall artifacts
5. create graph links across who / what / when / where / why / how
6. support provenance-rich recall for at least 5 signals across multiple sessions
7. demonstrate deterministic repeated output for the same inputs

## Why this scope is strong enough

It proves the central claim without overreaching:
- Signal Graph is not just storing memory blobs
- Signal Graph is not just summarizing
- Signal Graph is producing traceable, lossless, graph-linked recall artifacts

## Locked v1 non-goals

- broad connector coverage
- autonomous research / web discovery
- dashboard / rich UI

## Suggested v1 operator flow

A planning-friendly v1 workflow would look like:

1. `capture` or `submit-signal`
2. `annotate` or `normalize-signal`
3. `journalize` to produce markdown artifact + graph links
4. `recall` to answer provenance-rich lookup questions

Those names are illustrative only; final command naming can be chosen later during planning.

# Proposed Data Model Changes

These proposals should be treated as brownfield extensions to existing models, not a reason to discard the current architecture.

## 1. Extend raw source intake into a generalized signal record

Current repo evidence:
- `src/signal_graph/models/source.py`
- `src/signal_graph/storage/schema.sql`

Recommended additions:
- `signal_id`
- `origin_type` (`user`, `agent_artifact`, `external_reference`)
- `origin_channel` (cli, markdown, url, transcript, etc.)
- `source_ref` (path/url/object ref)
- `raw_content_ref` or inline raw text/payload pointer
- `captured_at`, `observed_at`, `published_at`
- `quality_flags`
- `content_hash`

## 2. Add agent provenance identity

Recommended normalized identity object or table:
- `agent_id`
- `host`
- `process_name`
- `runtime_family` (codex, claude-code, gemini, etc.)
- `session_id`
- `role`
- `invocation_context`

Signals created by humans would have this null or explicitly marked as human-originated.

## 3. Add signal journal / recall artifact model

The current memo artifact boundary in `src/signal_graph/services/explain.py` is a strong starting point, but v1 needs a new artifact class oriented around recall rather than trade explanation.

Recommended artifact fields:
- `artifact_id`
- `signal_id` or set of source signal ids
- `artifact_kind` (`journal_entry`, `recall_answer`, `summary`, `trace_view`)
- `artifact_path`
- `artifact_hash`
- `generated_at`
- `derivation_policy`
- `provenance_refs`

## 4. Add explicit graph topology for who / what / when / where / why / how

Recommended graphable dimensions:
- **WHO**: person / agent / organization / actor
- **WHAT**: topic / entity / artifact / event
- **WHEN**: timestamps / session / sequence / validity window
- **WHERE**: file / URL / host / workspace / channel
- **WHY**: goal / intent / decision / contradiction / rationale
- **HOW**: procedure / transformation / command / derivation step

This should not be treated as decorative metadata. It should define recall pivots and path explanations.

## 5. Preserve the dual-store architecture

The existing split remains attractive:
- **SQLite** for deterministic canonical records and artifact metadata
- **Neo4j** for explicit recall paths and topology traversal
- **filesystem markdown** for agent-usable artifacts and human inspectability

That is a competitive strength and should be preserved.

# Agent Integration Surface

This belongs mostly to later roadmap stages, but the research suggests Signal Graph should prepare a clear agent-facing surface early.

## Recommended future skills / runbooks

The user's desired outcome also implies an **MCP server surface** for recall/summarization, even if richer integration work remains later in the roadmap.


1. **install-signal-graph**  
   Agent installs dependencies, initializes local state, verifies doctor checks.

2. **capture-signal**  
   Agent persists a user signal or action artifact with required provenance metadata.

3. **recall-signal**  
   Agent retrieves relevant journal artifacts and provenance paths before answering.

4. **provenance-audit**  
   Agent validates that a recall artifact traces back to raw sources and graph links.

5. **sync-artifacts**  
   Agent updates markdown artifacts and verifies hashes/references remain valid.

## Recommended instructions for later roadmap stages

- always read relevant signal artifacts before answering
- never summarize away raw-signal recoverability
- distinguish raw signal, graph implication, and assistant inference
- attach agent identity on writes
- attach explicit references on recalls

## Why this matters competitively

GBrain is compelling partly because it ships a playbook, not just commands. Signal Graph should do the same, but tuned for provenance and recall discipline rather than general “brain” upkeep.

# Risks and Non-Goals

## Major risks

1. **Generic memory-platform creep**  
   Signal Graph could become indistinguishable from broad “AI memory” systems if it does not anchor on provenance and losslessness.

2. **Scope sprawl through connectors**  
   Supporting many ingestion sources too early would dilute the first milestone.

3. **Premature automation**  
   Autonomous web research or auto-discovery would undermine the deterministic, auditable posture too early.

4. **Topology theater**  
   If who / what / when / where / why / how are only labels and not retrieval pivots, the system will feel conceptually rich but practically weak.

5. **Over-optimizing compression before proof**  
   The current evidence suggests raw retention is the safer differentiator for early quality proof.

## Explicit non-goals already locked for v1

- broad connector coverage
- autonomous research / web discovery
- dashboard / rich UI

# Source Notes

1. **Signal Graph local README and architecture docs**  
   Accessed April 11, 2026. These establish that the repo is already CLI-first, provenance-aware, deterministic, and split across SQLite, Neo4j, and filesystem artifacts.

2. **Signal Graph analyst/agent guide**  
   Accessed April 11, 2026. This confirms explicit workflow ordering, provenance rules, and markdown artifact output.

3. **MemPalace README**  
   Accessed April 11, 2026. Public framing emphasizes raw/verbatim retention, structured findability, and local-first memory.

4. **GBrain README**  
   Accessed April 11, 2026. Public framing emphasizes agent-operated installation, markdown/git source of truth, and integration recipes.

5. **GitHubAwesome article published December 14, 2025**  
   Accessed April 11, 2026. The roundup suggests active open-source demand around agent memory, orchestration, MCP integration, and graph/code-aware systems.
