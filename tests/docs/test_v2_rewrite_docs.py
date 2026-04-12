from __future__ import annotations

from pathlib import Path


def test_top_level_docs_frame_v2_as_memory_and_decision_support():
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
    assert "v2" in texts["docs_index"]
    assert "owner" in texts["architecture"]
    assert "correction" in texts["architecture"]
    assert "http" in texts["architecture"]
    assert "stdio" in texts["architecture"]
    assert "v1 trading-research workflow" in texts["readme"]
    assert "superseded legacy lane" in texts["product"]


def test_required_v2_adrs_exist_and_cover_acceptance_topics():
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
