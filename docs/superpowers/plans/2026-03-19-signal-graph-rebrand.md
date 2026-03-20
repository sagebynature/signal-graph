# Signal Graph Rebrand Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebrand the project from `signal-graph` to `Signal Graph` across code, tests, docs, skills, and repository-facing naming.

**Architecture:** Apply a hard-cut rename so the active codebase, CLI, package namespace, local state paths, and docs all use one consistent identity. Preserve historical planning docs only as archival material, but update active docs, runbooks, ADRs, and tests to the new name. Rename the working directory only after code and docs verify cleanly.

**Tech Stack:** Python 3.12, uv, Typer, pytest, ty, Markdown docs, shell filesystem operations

---

### Task 1: Add Rebrand Regression Coverage

**Files:**
- Modify: `tests/cli/test_version_command.py`
- Modify: `tests/cli/test_make_targets.py`
- Modify: `tests/cli/test_init_command.py`
- Modify: `tests/cli/test_submit_command.py`
- Modify: `tests/cli/test_research_command.py`
- Modify: `tests/cli/test_ingest_command.py`
- Modify: `tests/cli/test_explain_command.py`
- Modify: `tests/e2e/test_manual_event_flow.py`

- [ ] **Step 1: Update tests to expect the new CLI name and local state path**

```python
assert result.stdout == "signal-graph 0.1.0\n"
assert Path(".signal-graph/artifacts").is_dir()
```

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `uv run pytest tests/cli/test_version_command.py tests/cli/test_make_targets.py tests/e2e/test_manual_event_flow.py -v`
Expected: FAIL because the implementation still uses `signal-graph` and `.signal-graph`

- [ ] **Step 3: Commit**

```bash
git add tests/cli/test_version_command.py tests/cli/test_make_targets.py tests/cli/test_init_command.py tests/cli/test_submit_command.py tests/cli/test_research_command.py tests/cli/test_ingest_command.py tests/cli/test_explain_command.py tests/e2e/test_manual_event_flow.py
git commit -m "test: add signal-graph rebrand expectations"
```

### Task 2: Rename Packaging, CLI, Imports, And Local Paths

**Files:**
- Modify: `pyproject.toml`
- Modify: `Makefile`
- Rename: `src/signal_graph/` -> `src/signal_graph/`
- Modify: all Python imports under `src/` and `tests/`
- Modify: local state path constants and path assertions under `src/` and `tests/`

- [ ] **Step 1: Rename the package directory**

Run: `mv src/signal_graph src/signal_graph`
Expected: source tree now lives under `src/signal_graph`

- [ ] **Step 2: Update packaging metadata and console script**

```toml
[project]
name = "signal-graph"
description = "CLI scaffold for signal-graph"

[project.scripts]
signal-graph = "signal_graph.cli.main:app"

[tool.hatch.build.targets.wheel]
packages = ["src/signal_graph"]
```

- [ ] **Step 3: Update imports, package docstrings, CLI output strings, and local paths**

```python
DEFAULT_PROJECT_DIR = Path(".signal-graph")
print(f"signal-graph {package_version('signal-graph')}")
```

- [ ] **Step 4: Update command expectations in the Makefile**

```makefile
doctor:
	uv run signal-graph doctor
```

- [ ] **Step 5: Run focused tests to verify they pass**

Run: `uv run pytest tests/cli/test_version_command.py tests/cli/test_make_targets.py tests/e2e/test_manual_event_flow.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml Makefile src tests uv.lock
git commit -m "refactor: rename package and cli to signal-graph"
```

### Task 3: Rebrand Active Documentation And Skill Paths

**Files:**
- Modify: `README.md`
- Rename: `docs/runbooks/agent-usage.md` -> `docs/runbooks/analyst-agent-guide.md` if not already applied
- Rename: `docs/runbooks/local-development.md` -> `docs/runbooks/operator-guide.md` if not already applied
- Create/Modify: `docs/overview/product.md`
- Create/Modify: `docs/architecture/system-overview.md`
- Create/Modify: `docs/adr/ADR-0001-cli-first-provenance-workflow.md`
- Create/Modify: `docs/adr/ADR-0002-sqlite-plus-neo4j-separation.md`
- Create/Modify: `docs/adr/ADR-0003-agent-skill-and-command-order.md`
- Rename: `skills/signal-graph/` -> `skills/signal-graph/`
- Modify: `tests/docs/test_skill_references.py`

- [ ] **Step 1: Rename the skill directory**

Run: `mv skills/signal-graph skills/signal-graph`
Expected: skill file now lives under `skills/signal-graph/SKILL.md`

- [ ] **Step 2: Update the skill test to the new path**

```python
text = Path("skills/signal-graph/SKILL.md").read_text()
```

- [ ] **Step 3: Rebrand active docs to `Signal Graph`**

```md
# Signal Graph
`signal-graph` is a CLI-first, provenance-aware trading research toolkit...
```

- [ ] **Step 4: Add a migration note in the README for archived `signal-graph` references**

```md
Older planning documents may still refer to `signal-graph`; they describe the same project before the rebrand.
```

- [ ] **Step 5: Run the docs-focused test**

Run: `uv run pytest tests/docs/test_skill_references.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add README.md docs skills tests/docs/test_skill_references.py
git commit -m "docs: rebrand project documentation to signal-graph"
```

### Task 4: Clean Up Repo References And Verify End-To-End

**Files:**
- Modify: remaining references found by search
- Verify: repo root working directory rename after tests pass

- [ ] **Step 1: Search for stale active references**

Run: `rg -n "signal-graph|signal_graph|\\.signal-graph|skills/signal-graph" .`
Expected: only archived or intentionally historical references remain

- [ ] **Step 2: Run the full verification suite**

Run: `uv run pytest -v`
Expected: PASS

- [ ] **Step 3: Run type checking**

Run: `uv run ty check`
Expected: PASS

- [ ] **Step 4: Smoke-test the rebranded CLI**

Run: `uv run signal-graph version`
Expected: prints `signal-graph 0.1.0`

Run: `uv run signal-graph doctor`
Expected: prints config and environment checks

- [ ] **Step 5: Rename the repo working directory**

Run: `cd .. && mv signal-graph signal-graph`
Expected: repository directory name matches the new product slug

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "chore: complete signal-graph rebrand"
```
