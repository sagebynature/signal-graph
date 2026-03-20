from __future__ import annotations

import pytest

from signal_graph.services.scoring_policy import get_scoring_policy


def test_get_scoring_policy_uses_local_config_override(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    project_dir = tmp_path / ".signal-graph"
    project_dir.mkdir()
    (project_dir / "config.toml").write_text(
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
        ["SUPPLIES_TO_AFFECTED"], event_type="export_control", direction="negative"
    )

    assert resolved.description == "custom upstream supplier exposure"
    assert resolved.base_score == 0.61
    assert resolved.timing_window == "immediate"


def test_get_scoring_policy_rejects_invalid_timing_window(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    project_dir = tmp_path / ".signal-graph"
    project_dir.mkdir()
    (project_dir / "config.toml").write_text(
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
