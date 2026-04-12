from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from signal_graph.services.journal import create_journal_signal, persist_journal_signal
from signal_graph.storage.sqlite import SqliteStore


def _send_framed_json(process: subprocess.Popen[bytes], payload: dict) -> None:
    assert process.stdin is not None
    body = json.dumps(payload).encode("utf-8")
    process.stdin.write(f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8"))
    process.stdin.write(body)
    process.stdin.flush()


def _read_framed_json(process: subprocess.Popen[bytes]) -> dict:
    assert process.stdout is not None
    content_length = None
    while True:
        line = process.stdout.readline()
        if not line:
            raise AssertionError("MCP server closed stdout unexpectedly")
        if line in {b"\r\n", b"\n"}:
            break
        decoded = line.decode("utf-8").strip()
        key, _, value = decoded.partition(":")
        if key.lower() == "content-length":
            content_length = int(value.strip())
    assert content_length is not None
    payload = process.stdout.read(content_length)
    return json.loads(payload.decode("utf-8"))


def test_stdio_mcp_server_supports_initialize_and_tool_calls(tmp_path):
    store = SqliteStore(tmp_path / ".signal-graph" / "signal_graph.db")
    store.init_db()
    signal = create_journal_signal(
        text="External host validation signal",
        origin_type="user",
        source_name="manual",
        what_refs=["validation"],
    )
    persist_journal_signal(store, signal)

    process = subprocess.Popen(
        [sys.executable, "-m", "signal_graph.mcp.server"],
        cwd=tmp_path,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        _send_framed_json(
            process,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-03-26"},
            },
        )
        initialize = _read_framed_json(process)
        assert initialize["result"]["protocolVersion"] == "2025-03-26"

        _send_framed_json(
            process,
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
        )

        _send_framed_json(
            process,
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        tools = _read_framed_json(process)
        names = {tool["name"] for tool in tools["result"]["tools"]}
        assert "signal_graph_list_signals" in names

        _send_framed_json(
            process,
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "signal_graph_list_signals",
                    "arguments": {"query": "validation"},
                },
            },
        )
        response = _read_framed_json(process)
        assert response["result"]["isError"] is False
        assert response["result"]["structuredContent"]["matches"][0]["signal"]["signal_id"] == signal.signal_id
    finally:
        process.terminate()
        process.wait(timeout=10)
