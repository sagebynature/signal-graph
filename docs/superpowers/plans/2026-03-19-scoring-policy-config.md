# Scoring Policy Config Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make scoring policy configurable from `.signal-graph/config.toml`, ship a checked-in example file, and document the feature with copyable examples.

**Architecture:** Keep the built-in scoring policy as the default source of truth, then merge optional local TOML overrides into the typed `ScoringPolicy` model at load time. All consumers continue to resolve policy through `get_scoring_policy()`, while docs and example files explain the config shape, precedence, and failure behavior.

**Tech Stack:** Python 3.12, Pydantic models, TOML config loading, pytest, Typer CLI docs, Markdown documentation.

---

### Task 1: Add Failing Tests For Config Parsing And Merge

**Files:**
- Create: `tests/services/test_scoring_policy_config.py`
- Modify: `tests/services/test_scoring_policy.py`
- Test: `tests/services/test_scoring_policy_config.py`

- [ ] **Step 1: Write the failing config parse test**

```python
def test_get_scoring_policy_uses_local_config_override(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".signal-graph").mkdir()
    (tmp_path / ".signal-graph/config.toml").write_text(
        """
        [scoring_policy]

        [[scoring_policy.paths]]
        relationship_path = ["SUPPLIES_TO_AFFECTED"]
        description = "custom upstream supplier exposure"
        base_score = 0.61
        timing_window = "immediate"
        """
    )

    resolved = get_scoring_policy().resolve(
        ["SUPPLIES_TO_AFFECTED"], event_type="capex_cut", direction="negative"
    )

    assert resolved.description == "custom upstream supplier exposure"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/services/test_scoring_policy_config.py -q`
Expected: FAIL because local config is ignored

- [ ] **Step 3: Write the failing malformed-config test**

```python
def test_get_scoring_policy_rejects_invalid_timing_window(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".signal-graph").mkdir()
    (tmp_path / ".signal-graph/config.toml").write_text(
        """
        [scoring_policy]

        [[scoring_policy.paths]]
        relationship_path = ["HOLDS"]
        description = "bad rule"
        base_score = 0.5
        timing_window = "later"
        """
    )

    with pytest.raises(ValueError, match="timing_window"):
        get_scoring_policy()
```
```

- [ ] **Step 4: Run test to verify it fails**

Run: `uv run pytest tests/services/test_scoring_policy_config.py -q`
Expected: FAIL because invalid config is not yet validated

- [ ] **Step 5: Commit**

```bash
git add tests/services/test_scoring_policy.py tests/services/test_scoring_policy_config.py
git commit -m "test: cover scoring policy config overrides"
```

### Task 2: Implement Config Parsing And Merge

**Files:**
- Modify: `src/signal_graph/config.py`
- Modify: `src/signal_graph/models/policy.py`
- Modify: `src/signal_graph/services/scoring_policy.py`
- Test: `tests/services/test_scoring_policy_config.py`

- [ ] **Step 1: Add typed config extraction helper in `config.py`**

```python
def get_scoring_policy_config() -> dict[str, Any] | None:
    config = load_config() or {}
    scoring_policy = config.get("scoring_policy")
    return scoring_policy if isinstance(scoring_policy, dict) else None
```

- [ ] **Step 2: Add merge helpers in `models/policy.py`**

```python
def merged_with(self, override: "ScoringPolicy") -> "ScoringPolicy":
    ...
```

Include exact-match replacement for:
- `relationship_path`
- `event_type + direction`
- `event_type + direction + relationship_path`

- [ ] **Step 3: Parse config into typed policy models in `scoring_policy.py`**

```python
def load_configured_scoring_policy() -> ScoringPolicy | None:
    raw_config = get_scoring_policy_config()
    if raw_config is None:
        return None
    return ScoringPolicy.model_validate(raw_config)
```

- [ ] **Step 4: Merge configured overrides onto built-in defaults**

```python
def get_scoring_policy() -> ScoringPolicy:
    configured = load_configured_scoring_policy()
    if configured is None:
        return _DEFAULT_SCORING_POLICY
    return _DEFAULT_SCORING_POLICY.merged_with(configured)
```

- [ ] **Step 5: Run focused tests**

Run: `uv run pytest tests/services/test_scoring_policy.py tests/services/test_scoring_policy_config.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/signal_graph/config.py src/signal_graph/models/policy.py src/signal_graph/services/scoring_policy.py tests/services/test_scoring_policy.py tests/services/test_scoring_policy_config.py
git commit -m "feat: load scoring policy from local config"
```

### Task 3: Prove Config-Driven Behavior In Ranking And Explanation

**Files:**
- Modify: `tests/cli/test_rank_command.py`
- Modify: `tests/cli/test_explain_command.py`
- Test: `tests/cli/test_rank_command.py`
- Test: `tests/cli/test_explain_command.py`

- [ ] **Step 1: Write the failing rank override test**

```python
def test_rank_uses_local_export_control_policy(tmp_path, monkeypatch):
    ...
    (tmp_path / ".signal-graph/config.toml").write_text(
        '''
        [scoring_policy]

        [[scoring_policy.events]]
        event_type = "export_control"
        direction = "negative"

        [[scoring_policy.events.overrides]]
        relationship_path = ["HOLDS"]
        base_score = 0.72
        timing_window = "immediate"
        rationale = "For a negative `export_control`, sector ETF exposure can move immediately."
        '''
    )
    ...
    assert candidates[1]["ticker"] == "SMH"
```

- [ ] **Step 2: Run the rank test to verify it fails**

Run: `uv run pytest tests/cli/test_rank_command.py -q`
Expected: FAIL because the new event policy is not yet visible to the resolver

- [ ] **Step 3: Write the failing explain rationale test**

```python
def test_explain_uses_local_policy_rationale(tmp_path, monkeypatch):
    ...
    assert "For a negative `export_control`" in result.stdout
```

- [ ] **Step 4: Run the explain test to verify it fails**

Run: `uv run pytest tests/cli/test_explain_command.py -q`
Expected: FAIL because the memo still uses only built-in rationale

- [ ] **Step 5: Ensure current consumers use the merged policy**

No feature additions should be needed if Task 2 was implemented cleanly; fix any consumer assumptions revealed by the failing tests.

- [ ] **Step 6: Run focused CLI tests**

Run: `uv run pytest tests/cli/test_rank_command.py tests/cli/test_explain_command.py -q`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add tests/cli/test_rank_command.py tests/cli/test_explain_command.py
git commit -m "test: cover config-driven ranking policy"
```

### Task 4: Add Example File And Documentation

**Files:**
- Create: `docs/examples/scoring-policy.example.toml`
- Modify: `README.md`
- Modify: `docs/runbooks/operator-guide.md`
- Modify: `docs/runbooks/analyst-agent-guide.md`
- Test: `tests/docs/` if coverage is added

- [ ] **Step 1: Add checked-in example file**

Include:
- baseline path policies
- `capex_cut` override example
- `export_control` example
- comment lines explaining precedence

- [ ] **Step 2: Update README**

Add a short “Customizing Scoring Policy” section with:
- config location
- precedence rule
- one short example
- pointer to the full example file

- [ ] **Step 3: Update operator guide**

Document:
- `.signal-graph/config.toml` location
- merge rules
- failure behavior on malformed config
- two copyable examples

- [ ] **Step 4: Update analyst guide**

Document:
- local policy changes can alter rank order
- local policy changes can alter memo rationale
- agents should report when non-default scoring policy is active

- [ ] **Step 5: Run doc-adjacent verification**

Run: `uv run pytest tests -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add docs/examples/scoring-policy.example.toml README.md docs/runbooks/operator-guide.md docs/runbooks/analyst-agent-guide.md
git commit -m "docs: add scoring policy configuration examples"
```

### Task 5: Final Verification

**Files:**
- Verify only

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest tests -q`
Expected: PASS

- [ ] **Step 2: Run type checks**

Run: `uv run ty check`
Expected: `All checks passed!`

- [ ] **Step 3: Smoke-test merged policy behavior**

Run:

```bash
uv run signal-graph init
cat .signal-graph/config.toml
uv run signal-graph rank --event <graph_event_id>
uv run signal-graph explain --event <graph_event_id> --candidate <ticker>
```

Expected:
- local config changes ranking order or rationale as intended
- malformed config raises a clear message

- [ ] **Step 4: Commit if final adjustments were needed**

```bash
git add -A
git commit -m "chore: finalize scoring policy config support"
```
