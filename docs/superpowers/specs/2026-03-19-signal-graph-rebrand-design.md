# Signal Graph Rebrand Design

**Date:** 2026-03-19

## Goal

Rebrand the project from `signal-graph` / `signal_graph` to `Signal Graph` / `signal-graph` / `signal_graph` across the full repo, including:

- product-facing naming
- Python package and import paths
- CLI command name
- local state directory names
- skill and documentation paths
- repository name and slug references

## Scope

This is a hard-cut rebrand. The old `signal-graph` identity will not be preserved as a compatibility alias unless implementation uncovers a concrete blocker.

The rebrand covers:

- display name: `Signal Graph`
- CLI command: `signal-graph`
- Python package: `signal_graph`
- local state directory: `.signal-graph`
- skill path: `skills/signal-graph/`
- docs, README, ADRs, tests, and runbooks
- repo slug references currently tied to `signal-graph`

## Non-Goals

- redesigning the product workflow itself
- changing the command order or provenance rules
- introducing backward-compatibility shims unless strictly necessary
- changing the underlying storage or graph architecture

## Decision

Use a single-pass hard rebrand rather than a staged or compatibility-first migration.

## Why

The repository is still early-stage, local-first, and primarily operated by developers and agents within the repo. That makes naming consistency more valuable than preserving a legacy compatibility layer.

Keeping both names alive would create unnecessary ambiguity in:

- command examples
- docs and onboarding
- import paths
- skill references
- local artifact paths

## User-Facing Naming

- Product name: `Signal Graph`
- Command name: `signal-graph`
- Python package/module: `signal_graph`
- Local data directory: `.signal-graph`

## Technical Implications

### Packaging

`pyproject.toml` must be updated so the package name and console script entrypoint use `signal-graph` and `signal_graph`.

### Source Tree

The package directory `src/signal_graph/` should be renamed to `src/signal_graph/`, and all imports updated accordingly.

### Tests

Tests must be updated to use:

- `signal_graph` imports
- `signal-graph` CLI command expectations
- `.signal-graph` local paths

### Documentation

All docs should consistently describe the product as `Signal Graph`, except where historical plan documents explicitly preserve the old name as archival context.

### Skills

The skill path should move from `skills/signal-graph/` to `skills/signal-graph/`, with references updated accordingly.

## Repository Naming

The preferred repo slug is `signal-graph`.

The working directory rename should happen after code and docs are green, because changing the directory too early adds avoidable friction during the implementation pass.

## Migration Notes

This is a clean-break rename. The README should contain a short migration note explaining that older `signal-graph` references in prior commits or archived planning docs refer to the same project lineage.

## Verification Requirements

The implementation must prove:

- package imports resolve under `signal_graph`
- `uv run pytest -v` passes
- `uv run ty check` passes
- `uv run signal-graph version` works
- `uv run signal-graph doctor` works
- end-to-end CLI flow still writes outputs under `.signal-graph/`

## Risks

### Incomplete rename

The biggest risk is leaving stale `signal-graph` references in tests, docs, or command strings.

### Path drift

Renaming package and artifact paths simultaneously can create subtle failures if tests or smoke checks still point at `.signal-graph`.

### Archived plan confusion

Historical documents may retain the old name. That is acceptable if clearly framed as legacy planning material rather than current product naming.

## Acceptance Criteria

- The active codebase, docs, and tests use the `Signal Graph` naming consistently
- The CLI command is `signal-graph`
- The Python package namespace is `signal_graph`
- The local state path is `.signal-graph`
- The repo documentation explains the rename clearly
