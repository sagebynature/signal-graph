from __future__ import annotations

from pathlib import Path


def test_skill_mentions_provenance_and_command_order():
    text = Path("skills/signal-graph/SKILL.md").read_text()
    assert "provenance" in text.lower()
    assert "normalize" in text.lower()
    assert "research" in text.lower()
    assert "ingest" in text.lower()
