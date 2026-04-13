from __future__ import annotations

from pathlib import Path


def test_skill_mentions_provenance_and_supported_command_surface():
    text = Path("skills/signal-graph/SKILL.md").read_text().lower()
    assert "provenance" in text
    assert "capture-signal" in text
    assert "journalize-signal" in text
    assert "recall-signal" in text
    assert "bootstrap-describe" in text
