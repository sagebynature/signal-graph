from __future__ import annotations

from pathlib import Path


def test_top_level_docs_frame_current_memory_system_without_legacy_runtime_story():
    texts = {
        "readme": Path("README.md").read_text().lower(),
        "docs_index": Path("docs/README.md").read_text().lower(),
        "product": Path("docs/overview/product.md").read_text().lower(),
        "architecture": Path("docs/architecture/system-overview.md")
        .read_text()
        .lower(),
    }

    assert "memory and decision-support system" in texts["readme"]
    assert "memory and decision-support system" in texts["product"]
    assert "bootstrap-describe" in texts["docs_index"]
    assert "capture-signal" in texts["architecture"]
    assert "journal_signals" in texts["architecture"]
    assert "brownfield" not in texts["readme"]
    assert "v1" not in texts["readme"]
    assert "rewrite track" not in texts["readme"]
    assert "superseded legacy lane" not in texts["product"]


def test_required_adrs_exist_and_cover_current_acceptance_topics():
    expected = {
        "docs/adr/ADR-0004-v2-memory-ontology.md": (
            "owner",
            "actor",
            "artifact",
            "correction",
            "whyinference",
        ),
        "docs/adr/ADR-0005-v2-storage-of-record-split.md": (
            "append-only",
            "raw artifacts",
            "derived",
            "graph",
            "source truth",
        ),
        "docs/adr/ADR-0006-v2-mcp-transport-parity.md": (
            "stdio",
            "http",
            "parity",
            "schema",
            "error model",
        ),
        "docs/adr/ADR-0007-v2-hook-ingestion-envelope.md": (
            "hook",
            "event envelope",
            "owner",
            "actor",
            "pre-action",
        ),
        "docs/adr/ADR-0008-v2-http-trusted-environment-boundary.md": (
            "trusted",
            "http",
            "stdio",
            "mvp",
            "multi-tenant",
        ),
    }

    for path_str, tokens in expected.items():
        path = Path(path_str)
        assert path.exists()
        text = path.read_text().lower()
        assert "accepted" in text
        for token in tokens:
            assert token in text
