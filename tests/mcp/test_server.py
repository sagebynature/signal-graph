from __future__ import annotations

import json
from pathlib import Path

from signal_graph.mcp.server import handle_message
from tests.cli._journal_helpers import install_fake_journal_graph_client


def test_initialize_negotiates_protocol_version(tmp_path):
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-03-26"},
        },
        store_path=tmp_path / "signal_graph.db",
        artifact_dir=tmp_path / "artifacts",
    )

    assert response is not None
    assert response["result"]["protocolVersion"] == "2025-03-26"
    assert response["result"]["capabilities"]["tools"]["listChanged"] is False


def test_tools_list_exposes_signal_graph_tools(tmp_path):
    response = handle_message(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        store_path=tmp_path / "signal_graph.db",
        artifact_dir=tmp_path / "artifacts",
    )

    assert response is not None
    names = {tool["name"] for tool in response["result"]["tools"]}
    assert {
        "signal_graph_capture_signal",
        "signal_graph_journalize_signal",
        "signal_graph_recall_signal",
        "signal_graph_list_signals",
    } <= names


def test_tools_call_recall_returns_structured_content(monkeypatch, tmp_path):
    install_fake_journal_graph_client(monkeypatch)
    store_path = tmp_path / "signal_graph.db"
    artifact_dir = tmp_path / "artifacts"
    capture = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "signal_graph_capture_signal",
                "arguments": {
                    "text": "Agent deployment signal",
                    "origin_type": "agent_artifact",
                    "source_name": "codex",
                    "runtime_family": "codex",
                    "session_id": "session-1",
                    "what": ["deployment"],
                    "where": ["notes/release.md"],
                },
            },
        },
        store_path=store_path,
        artifact_dir=artifact_dir,
    )
    assert capture is not None
    signal_id = capture["result"]["structuredContent"]["signal_id"]
    handle_message(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "signal_graph_journalize_signal",
                "arguments": {"signal_id": signal_id},
            },
        },
        store_path=store_path,
        artifact_dir=artifact_dir,
    )

    recall = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "signal_graph_recall_signal",
                "arguments": {"query": "deployment", "runtime_family": "codex"},
            },
        },
        store_path=store_path,
        artifact_dir=artifact_dir,
    )

    assert recall is not None
    result = recall["result"]
    assert result["isError"] is False
    assert "Signal Recall" in result["content"][0]["text"]
    assert result["structuredContent"]["signal_ids"] == [signal_id]
    assert result["structuredContent"]["matches"][0]["explanation"]["score_components"]
    assert Path(result["structuredContent"]["artifact_path"]).is_file()


def test_tools_call_list_signals_supports_filter_only_lookup(monkeypatch, tmp_path):
    install_fake_journal_graph_client(monkeypatch)
    store_path = tmp_path / "signal_graph.db"
    artifact_dir = tmp_path / "artifacts"
    handle_message(
        {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "signal_graph_capture_signal",
                "arguments": {
                    "text": "User deployment signal",
                    "origin_type": "user",
                    "source_name": "manual",
                    "what": ["deployment"],
                },
            },
        },
        store_path=store_path,
        artifact_dir=artifact_dir,
    )

    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "signal_graph_list_signals",
                "arguments": {"origin_type": "user"},
            },
        },
        store_path=store_path,
        artifact_dir=artifact_dir,
    )

    assert response is not None
    result = response["result"]["structuredContent"]
    assert result["view"] == "ranked"
    assert len(result["matches"]) == 1
    assert result["matches"][0]["signal"]["origin_type"] == "user"


def test_tools_call_recall_supports_session_view(monkeypatch, tmp_path):
    install_fake_journal_graph_client(monkeypatch)
    store_path = tmp_path / "signal_graph.db"
    artifact_dir = tmp_path / "artifacts"
    for session_id, observed_at in (
        ("session-old", "2026-04-10T09:00:00+00:00"),
        ("session-new", "2026-04-11T09:00:00+00:00"),
    ):
        handle_message(
            {
                "jsonrpc": "2.0",
                "id": session_id,
                "method": "tools/call",
                "params": {
                    "name": "signal_graph_capture_signal",
                    "arguments": {
                        "text": f"Deployment signal for {session_id}",
                        "origin_type": "agent_artifact",
                        "source_name": "codex",
                        "runtime_family": "codex",
                        "session_id": session_id,
                        "observed_at": observed_at,
                        "what": ["deployment"],
                    },
                },
            },
            store_path=store_path,
            artifact_dir=artifact_dir,
        )
    list_response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {
                "name": "signal_graph_list_signals",
                "arguments": {"runtime_family": "codex"},
            },
        },
        store_path=store_path,
        artifact_dir=artifact_dir,
    )
    assert list_response is not None
    signal_ids = [
        match["signal"]["signal_id"]
        for match in list_response["result"]["structuredContent"]["matches"]
    ]
    for signal_id in signal_ids:
        handle_message(
            {
                "jsonrpc": "2.0",
                "id": f"j-{signal_id}",
                "method": "tools/call",
                "params": {
                    "name": "signal_graph_journalize_signal",
                    "arguments": {"signal_id": signal_id},
                },
            },
            store_path=store_path,
            artifact_dir=artifact_dir,
        )

    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "tools/call",
            "params": {
                "name": "signal_graph_recall_signal",
                "arguments": {"query": "deployment", "view": "session"},
            },
        },
        store_path=store_path,
        artifact_dir=artifact_dir,
    )

    assert response is not None
    result = response["result"]["structuredContent"]
    assert result["view"] == "session"
    assert result["session_groups"][0]["session_key"] == "session-new"
