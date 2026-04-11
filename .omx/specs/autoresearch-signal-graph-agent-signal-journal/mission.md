# Mission — signal-graph-agent-signal-journal

## Topic
Competitive and architectural research brief for evolving **Signal Graph** into a lossless, provenance-first agent signal journal with a roadmap toward recall/query and agent self-install/integration.

## Objective
Produce an evidence-backed research package that helps planning answer:
1. how Signal Graph can be competitive against adjacent agent-memory / graph-memory systems
2. what v1 of the **agent signal journal** should include and exclude
3. how the brownfield repo can evolve without losing its deterministic, provenance-first strengths
4. what agent-facing skills, instructions, and integration surfaces should ship later

## Required Research Questions

0. **Success-outcome fit**
   - Does the evolving plan actually support the user-facing promise that Signal Graph remembers user and agent actions, preserves who/what/when/where and only captures why when intention is clear?
   - What must be added so these signals can be queried/summarized via CLI and MCP, then fed into downstream signal interpreters that emit new signals?

1. **Competitive posture**
   - What do GBrain, MemPalace, and adjacent trending open-source projects do that users currently find compelling?
   - Which of those traits are essential, optional, or dangerous for Signal Graph to emulate?

2. **Architectural leverage**
   - Which existing Signal Graph boundaries (CLI, SQLite, Neo4j, markdown artifacts) are strengths to preserve?
   - What brownfield data-model and graph-model extensions are most likely needed for agent signal journaling?

3. **v1 scope clarity**
   - What is the smallest end-to-end v1 that still proves differentiation?
   - How should Signal Graph operationalize who / what / when / where / why / how without overbuilding?

4. **Agent integration surface**
   - What install/setup/integration instructions or skills should be designed for later roadmap stages?
   - How should agent identity (host/process/session/role) be handled in a way that is useful and deterministic?

## Deliverables

Write the following files into `.omx/specs/autoresearch-signal-graph-agent-signal-journal`:
- `report.md`
- `sources.json`

`report.md` must contain these exact headings:
- `# Competitive Assessment`
- `# Recommended v1 Scope`
- `# Proposed Data Model Changes`
- `# Agent Integration Surface`
- `# Risks and Non-Goals`
- `# Source Notes`

## Research Constraints

- Treat **Signal Graph** as the official product name.
- Respect locked v1 non-goals:
  - broad connector coverage
  - autonomous research / web discovery
  - dashboard / rich UI
- Preserve the user-approved roadmap order:
  1. agent signal journal
  2. high-quality recall/query
  3. agent self-install/setup/integration
- Primary evaluation bar is:
  - provenance traceability
  - losslessness
- Favor primary sources and project docs where possible.
- Use absolute dates when discussing current trend sources.

## Expected Output Style

Be concrete, comparative, and planning-friendly. Prefer repo-grounded recommendations over generic AI-memory advice.
