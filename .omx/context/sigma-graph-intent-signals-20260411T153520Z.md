# Context Snapshot: sigma-graph-intent-signals

- Task statement: Assess how Signal Graph could evolve into a Sigma Graph-style agent signal memory, provenance, and graph reasoning system inspired by gbrain and MemPalace, with autoresearch-ready outputs.
- Desired outcome: A clarified, competitive requirements brief for a first milestone and later planning.
- Stated solution: Extend Signal Graph from trading-event provenance into a broader multi-source agent signal capture/query/summary/graph system.
- Probable intent hypothesis: Build a deterministic, agent-native memory/provenance system that preserves signal quality, supports recall/query/summary, and can become category-leading.
- Known facts/evidence:
  - Current repo is CLI-first, SQLite + Neo4j, provenance-aware, deterministic, local-first.
  - Current pipeline is fetch/submit -> normalize -> research -> ingest -> rank -> explain.
  - Current connectors are stubbed; memo output is markdown artifact; graph reasoning boundary already exists.
  - User wants support for user signals, agent-generated signals, and external/public-reference signals with identity metadata.
  - User asked for competitive research input from architect + product-manager lens.
- Constraints:
  - Deep-interview mode only; no implementation in this lane.
  - Brownfield repo; should preserve provenance discipline.
  - Need agent-friendly markdown and graph-linked recallability.
- Unknowns/open questions:
  - First milestone exact proof point.
  - MVP non-goals boundaries.
  - Query/retrieval expectations.
  - Automation level for summarization and ingestion.
  - Decision autonomy OMX may take without confirmation.
- Decision-boundary unknowns:
  - Storage changes allowed for MVP?
  - Whether to optimize first for coding agents, research agents, or general personal knowledge workflows.
  - Whether external connectors are in MVP.
- Likely codebase touchpoints:
  - src/signal_graph/models/source.py
  - src/signal_graph/models/events.py
  - src/signal_graph/models/research.py
  - src/signal_graph/services/raw_items.py
  - src/signal_graph/services/normalize.py
  - src/signal_graph/services/research.py
  - src/signal_graph/graph/schema.py
  - src/signal_graph/cli/*.py
  - docs/architecture/system-overview.md


## Research refresh — 2026-04-11

### External market evidence
- GBrain GitHub repo presents itself as an AI-agent-operated "brain" where meetings, emails, tweets, calendar events, voice calls, and ideas flow into a searchable knowledge base that the agent reads before every response and writes to after every conversation.
- GBrain emphasizes agent-first installation, markdown files in a git repo as the knowledge model, local-first PGLite bootstrap, hybrid search, integration recipes, and explicit verification steps.
- MemPalace positions around raw verbatim retention, spatial organization, and benchmarked recall; it claims 96.6% LongMemEval R@5 in raw mode with zero API calls, while explicitly noting that its experimental compression mode regresses vs raw mode.
- MemPalace also highlights local/no-cloud operation plus plugin/MCP integration so the AI uses memory automatically rather than requiring manual CLI usage.
- GitHubAwesome latest items on 2026-04-11/10/09 suggest adjacent demand for: agent memory systems, codebase knowledge graphs, and copy-paste skills/MCP playbooks.

### Product implication hypothesis
The competitive opening for Signal Graph is not to become a generic consumer memory app. It is to own a more trustworthy niche: provenance-preserving, deterministic signal capture + recall + decision support for agents, with local artifacts, graph traceability, and integration ergonomics.
