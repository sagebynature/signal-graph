from __future__ import annotations

from pathlib import Path


def test_operational_automation_docs_reference_runtime_commands():
    texts = {
        "readme": Path("README.md").read_text(),
        "operator": Path("docs/runbooks/operator-guide.md").read_text(),
        "docs_index": Path("docs/README.md").read_text(),
        "integrations": Path("docs/integrations/README.md").read_text(),
    }

    for text in texts.values():
        assert "automation-describe" in text

    assert "integration-install --host claude-code" in texts["readme"]
    assert "integration-audit --host claude-code --json" in texts["operator"]
    assert "validated hosts" in texts["integrations"].lower()
