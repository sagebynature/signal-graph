# Neo4j AI Trading Assistant Design

**Date:** 2026-03-19

## Goal

Design a CLI-first, provenance-aware trading research assistant for agents and analysts that:

- supports premium structured feeds, public web research, and manual event submission
- normalizes all inputs into one canonical event pipeline
- uses Neo4j for relationship traversal and propagation reasoning
- generates ranked candidates and explainable discretionary trade memos
- can be operated safely by terminal-native agents such as Codex and Claude Code

## Revised Product Statement

The product is not a graph database with an assistant attached. The product is a trading decision-support workflow. Neo4j is one critical reasoning component inside that workflow.

The correct first shape is:

`A CLI-native event propagation and discretionary research assistant for equities and ETFs, backed by a provenance-aware ingestion pipeline and a Neo4j relationship graph.`

This replaces the earlier dashboard-first framing. The first-class user is now:

- a trading analyst working in a terminal
- an autonomous or semi-autonomous coding agent invoking shell commands under a `SKILL.md` protocol

## Critical Reassessment

The initial design was directionally correct but incomplete in three ways.

### 1. The graph was over-emphasized

The original design described the graph well but under-specified the event acquisition and research workflow. In practice, trading edge depends as much on event quality, dedupe, source trust, and provenance as it does on graph traversal.

### 2. Live events were treated as clean inputs

They are not. The system must handle:

- duplicates across multiple feeds
- conflicting headlines
- incomplete entity references
- stale or noisy public information
- analyst-pasted events that may require corroboration

### 3. Agent packaging was under-designed

If Codex and Claude Code are target operators, the product should be built as a local toolkit with machine-readable outputs, deterministic CLI commands, and an explicit skill protocol. It should not start as a web app that agents happen to automate.

## Why Neo4j Still Fits

Neo4j remains justified because the core value is explicit relationship traversal rather than semantic retrieval alone.

Graph value:

- model suppliers, customers, competitors, ETF membership, themes, geographies, commodities, and macro sensitivities
- traverse 1-hop and 2-hop propagation paths efficiently
- preserve explainability by returning concrete paths
- attach confidence and lag profiles to edges
- support both immediate spillover and slower drift in one system

Neo4j should not be the system of record for every artifact. It should be the reasoning layer for relationship-driven impact propagation.

## Product Interfaces

### Primary Interface: CLI

The assistant should be installed as a local command-line tool with a stable entrypoint such as `trade-graph`.

Example commands:

- `trade-graph doctor`
- `trade-graph init`
- `trade-graph fetch --source premium --since 5m`
- `trade-graph fetch --source web --query "semiconductor guidance cut"`
- `trade-graph submit --stdin`
- `trade-graph normalize --raw-item <id>`
- `trade-graph research --event-candidate <id>`
- `trade-graph ingest --event-candidate <id>`
- `trade-graph rank --event <id>`
- `trade-graph explain --event <id> --candidate SMH`
- `trade-graph review --queue pending`
- `trade-graph audit --event <id>`

### Local Development Tooling

The local development contract should be explicit:

- use `uv` for Python environment management, dependency installation, and command execution
- use `ty` for type checking
- use a top-level `Makefile` for the common workflows agents and humans need
- run Neo4j locally via Docker with bind-mounted host volumes for data durability and inspection

This matters for agent usage. A terminal-native agent needs deterministic setup commands and stable task entrypoints. `uv`, `ty`, and `make` provide that better than ad hoc shell instructions.

### Agent Interface: `SKILL.md`

Agents should not be expected to infer safe operating rules from scratch. The toolkit should ship with a carefully authored `SKILL.md` that tells an agent:

- when to fetch new data versus use existing ingested artifacts
- how to preserve provenance
- how to distinguish fact from implication from inference
- which commands to run in which order
- how to report confidence and timing windows
- when network access requires approval

### Deferred Interface: MCP

MCP remains a good later addition, but not the first surface. It should be treated as a thin adapter over the same core library and CLI semantics, not as the first architecture decision.

## Supported Source Modes

All three source modes should be supported, but not treated as operationally equivalent.

### Tier 1: Premium Structured Feeds

Examples:

- low-latency market news feeds
- earnings and filing APIs
- structured ETF holdings providers

Use:

- highest-trust intraday workflows
- minimal transformation before normalization

### Tier 2: Public Web And News Research

Examples:

- official press releases
- regulator sites
- public news pages
- company investor relations pages

Use:

- corroboration
- deeper discretionary research
- fallback when premium coverage is missing

### Tier 3: Manual Analyst Input

Examples:

- pasted headline text
- pasted meeting notes
- a user-submitted event hypothesis

Use:

- discretionary workflows
- idea capture
- exploratory or early research

## Operational Lanes

To avoid pretending all sources behave the same, the system should define three operating lanes.

### Fast Lane

- premium feeds only
- minimal research
- highest trust
- optimized for intraday spillover

### Balanced Lane

- premium plus public corroboration
- default operating mode
- suitable for most daily use

### Deep Research Lane

- manual input and analyst-triggered investigation
- slower but broader
- optimized for discretionary swing work

## Canonical Event Pipeline

All source modes feed one canonical pipeline:

`fetch -> normalize -> dedupe -> research -> trust score -> ingest -> rank -> explain`

This separation is critical. It prevents the system from mixing sourcing, inference, and storytelling in one opaque step.

### Pipeline Objects

#### `RawSourceItem`

The untouched fetched or submitted payload with source metadata.

Fields:

- `raw_item_id`
- `source_tier`
- `source_name`
- `source_url`
- `fetched_at`
- `published_at`
- `raw_text`
- `raw_payload`

#### `EventCandidate`

A normalized event hypothesis that has not yet been committed into graph reasoning.

Fields:

- `event_candidate_id`
- `title`
- `event_type`
- `direction`
- `primary_entities`
- `secondary_entities`
- `source_item_ids`
- `candidate_confidence`
- `candidate_status`

#### `ResearchBundle`

A collection of supporting documents, contradictions, extracted facts, and confidence metadata.

Fields:

- `research_bundle_id`
- `event_candidate_id`
- `supporting_documents`
- `contradictions`
- `entity_resolution_results`
- `evidence_spans`
- `research_confidence`
- `research_notes`

#### `GraphEvent`

A committed event eligible for graph propagation and ranking.

Fields:

- `graph_event_id`
- `event_candidate_id`
- `committed_at`
- `trust_score`
- `eligible_modes`
- `ingest_decision`

## Storage Model

The system should intentionally split storage responsibilities.

### Neo4j

Use for:

- `Company`, `ETF`, `Theme`, `Sector`, `Geography`, `Commodity`, `MacroFactor`
- event-to-entity links
- relationship traversal
- propagation path queries

### Structured Store

Use SQLite first for local portability.

Use for:

- raw source items
- research bundles
- audit logs
- dedupe state
- configuration snapshots
- realized outcomes

SQLite is the right MVP choice because this is a local CLI-first tool. It can be swapped later if multi-user or remote workflows matter.

### Local Neo4j Runtime

Neo4j should run locally in Docker rather than as a manually installed host dependency.

Requirements:

- Docker-managed Neo4j container
- bind-mounted local directories for `/data`, `/logs`, and optionally `/plugins`
- stable container naming and ports for predictable CLI configuration
- credentials and connection settings managed through local config

Bind mounts are preferable here because the intended users are local analysts and coding agents who may need to inspect, back up, or reset graph data directly.

### Filesystem Artifacts

Use for:

- cached fetched documents
- exported ranking results
- memo markdown
- prompt templates
- run manifests and debugging output

## Graph Model

### Nodes

- `Company`
- `ETF`
- `Theme`
- `Sector`
- `Geography`
- `Commodity`
- `MacroFactor`
- `GraphEvent`
- `Document`

### Relationships

- `SUPPLIES`
- `CUSTOMER_OF`
- `COMPETES_WITH`
- `MEMBER_OF`
- `EXPOSED_TO`
- `LINKED_TO`
- `DESCRIBED_BY`
- `IMPACTS`

### Relationship Properties

- `direction`
- `weight`
- `lag_profile`
- `confidence`
- `source_count`
- `last_verified`

Neo4j should store enough metadata to explain why a path exists and how quickly it is expected to matter.

## Reasoning And Scoring

The reasoner should return separate scores, not a single opaque number.

### Event Severity Score

Based on:

- source quality
- novelty
- explicitness
- magnitude or surprise
- market relevance

### Propagation Score

Based on:

- edge weights
- path length
- relationship type
- direction consistency
- ETF overlap
- similar historical outcomes

### Tradeability Score

Based on:

- liquidity
- spread and realized volatility
- time-of-day
- how much of the move may already be priced
- crowding or consensus

### Output Scores

- `fast_reaction_score`
- `follow_through_score`

### Timing Windows

The initial windows remain:

- `Immediate`: 5 minutes to same-session close
- `Short drift`: next session to 3 sessions
- `Multi-day`: 3 to 10 sessions

Traversal depth should be constrained by mode:

- intraday: mostly 1 hop
- swing: up to 2 hops

## Explanation Contract

The explainer must never generate unsupported narratives.

Each memo should explicitly separate:

- `Confirmed fact`
- `Graph implication`
- `Assistant inference`

Each memo should contain:

- thesis
- top path or paths
- supporting sources
- timing window
- confidence
- invalidation conditions
- lane used

## User And Agent Workflow

### Human Analyst Workflow

1. Fetch or submit an event.
2. Normalize and dedupe it.
3. Run research enrichment.
4. Ingest it if trust is sufficient.
5. Rank immediate and follow-through candidates.
6. Generate and review the memo.

### Agent Workflow

1. Check whether a matching `GraphEvent` already exists.
2. If not, fetch or submit the event into the canonical pipeline.
3. Persist every sourced artifact before explaining anything.
4. Ingest only when confidence and provenance thresholds are met.
5. Rank candidates.
6. Explain the requested candidate using stored evidence and graph paths only.

## Failure Modes

The main risks are:

- weak or stale relationship edges
- duplicate and conflicting source items
- entity resolution errors
- false confidence in public web material
- explanation layers outrunning the underlying evidence
- too many surfaced candidates for a human to process

Controls:

- explicit source tiers
- separate operating lanes
- aggressive dedupe
- review queue for ambiguous cases
- required provenance for all explanations
- traversal depth caps
- auditable artifacts on disk

## MVP Boundary

### In Scope

- CLI-first Python package
- local SQLite metadata store
- Neo4j relationship graph
- manual event submission
- at least one public-web connector
- premium connector interface with stub or mock implementation
- normalization, research, ingest, rank, and explain commands
- machine-readable JSON output plus markdown memo output
- packaged `SKILL.md` for agent operation

### Out of Scope

- dashboard-first product
- autonomous execution
- options strategy selection
- generalized multi-asset graph
- unconstrained agent browsing
- MCP as the primary interface

## Roadmap

### Phase 1

- core library
- CLI
- `uv`-managed Python environment
- `ty`-based type checking
- top-level `Makefile`
- local storage
- Dockerized Neo4j with bind-mounted volumes
- Neo4j integration
- manual and public-source workflows
- `SKILL.md`

### Phase 2

- stronger premium connectors
- better dedupe and outcome feedback
- improved relationship curation
- batch analyst workflows

### Phase 3

- MCP adapter
- optional service mode or daemon
- richer historical evaluation
- semi-systematic signal generation

## Summary

The revised design is stronger because it treats:

- event acquisition
- research
- ingestion
- graph reasoning
- explanation
- agent usage

as separate, auditable stages.

The result should be a local, agent-operable toolkit that can support both discretionary research and candidate generation without conflating sourcing and inference.
