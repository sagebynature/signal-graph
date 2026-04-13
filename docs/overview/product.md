# Product Overview

## Summary

`Signal Graph` is a local, CLI-first **memory and decision-support system** for humans and AI tools.

Its job is to preserve signals, artifact references, actor context, and later corrections with enough provenance to answer:

- what happened
- who or what produced the signal
- what evidence existed at the time
- why a later recall or explanation points back to that signal

## The Problem It Solves

Local work often leaves decisions scattered across terminals, notes, artifacts, and tool sessions. Signal Graph creates a consistent record that can be captured, journaled, recalled, and explained without relying on hidden cloud state.

## Product Shape

Signal Graph is intentionally:

- local-first
- CLI-native
- provenance-aware
- graph-backed for journaling and explanation
- MCP-compatible for host integrations

## Who It Is For

- developers running local agent workflows
- operators who need explicit runtime/bootstrap contracts
- humans and AI tools that need trustworthy recall over prior local work

## Primary Use Cases

### Signal capture
Record a structured signal with origin, source, session, and intent metadata.

### Graph journaling
Convert a captured signal into a graph-backed path that can later be inspected or reused.

### Recall and explanation
Query prior signals by phrase, session, source, or runtime and produce deterministic recall artifacts.

### Correction-aware memory
Preserve raw truth while allowing later interpretation and guidance to improve over time.

## What Makes It Different

- owner- and actor-aware provenance instead of anonymous transcript dumping
- local artifacts and inspectable state instead of hidden hosted memory
- explicit CLI and MCP contracts instead of implicit tool behavior
- recall artifacts that keep evidence and path context attached

## What This Cut Does Not Try To Do

- replace human judgment with opaque autonomous decisions
- offer a hardened public multi-tenant HTTP product
- erase raw evidence when interpretation changes
- preserve unsupported legacy workflow compatibility

## Read Next

- `../architecture/system-overview.md`
- `../runbooks/operator-guide.md`
- `../integrations/README.md`
