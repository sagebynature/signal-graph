from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from signal_graph.config import DEFAULT_PROJECT_DIR
from signal_graph.services.journal import (
    create_journal_signal,
    journalize_signal,
    parse_intent_status,
    parse_optional_datetime,
    parse_origin_type,
    recall_signals,
)
from signal_graph.storage.sqlite import SqliteStore

SUPPORTED_PROTOCOL_VERSIONS = {"2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25"}
DEFAULT_PROTOCOL_VERSION = "2025-03-26"
SERVER_INFO = {
    "name": "signal-graph-mcp",
    "title": "Signal Graph MCP Server",
    "version": "0.1.0",
}


def build_tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "signal_graph_capture_signal",
            "title": "Capture Signal",
            "description": "Persist a journal signal with provenance metadata.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "origin_type": {
                        "type": "string",
                        "enum": ["user", "agent_artifact", "external_reference"],
                    },
                    "source_name": {"type": "string"},
                    "source_url": {"type": "string"},
                    "source_ref": {"type": "string"},
                    "raw_payload": {"type": "string"},
                    "observed_at": {"type": "string"},
                    "published_at": {"type": "string"},
                    "host": {"type": "string"},
                    "process": {"type": "string"},
                    "runtime_family": {"type": "string"},
                    "session_id": {"type": "string"},
                    "role": {"type": "string"},
                    "workspace_path": {"type": "string"},
                    "intent_status": {
                        "type": "string",
                        "enum": ["explicit", "inferred", "unknown"],
                    },
                    "why": {"type": "string"},
                    "who": {"type": "array", "items": {"type": "string"}},
                    "what": {"type": "array", "items": {"type": "string"}},
                    "where": {"type": "array", "items": {"type": "string"}},
                    "how": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["text", "origin_type", "source_name"],
            },
        },
        {
            "name": "signal_graph_journalize_signal",
            "title": "Journalize Signal",
            "description": "Write graph pivots for a captured journal signal.",
            "inputSchema": {
                "type": "object",
                "properties": {"signal_id": {"type": "string"}},
                "required": ["signal_id"],
            },
        },
        {
            "name": "signal_graph_recall_signal",
            "title": "Recall Signals",
            "description": "Query journal signals and produce a provenance-rich recall artifact.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                    "origin_type": {
                        "type": "string",
                        "enum": ["user", "agent_artifact", "external_reference"],
                    },
                    "session_id": {"type": "string"},
                    "runtime_family": {"type": "string"},
                    "source_name": {"type": "string"},
                },
                "required": ["query"],
            },
        },
        {
            "name": "signal_graph_list_signals",
            "title": "List Signals",
            "description": "List journal signals matching optional provenance filters.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                    "origin_type": {
                        "type": "string",
                        "enum": ["user", "agent_artifact", "external_reference"],
                    },
                    "session_id": {"type": "string"},
                    "runtime_family": {"type": "string"},
                    "source_name": {"type": "string"},
                },
            },
        },
    ]


def handle_message(
    message: dict[str, Any],
    *,
    store_path: Path | None = None,
    artifact_dir: Path | None = None,
) -> dict[str, Any] | None:
    method = message.get("method")
    message_id = message.get("id")
    params = message.get("params") or {}
    store = SqliteStore(store_path or DEFAULT_PROJECT_DIR / "signal_graph.db")
    if method == "initialize":
        protocol_version = str(params.get("protocolVersion") or DEFAULT_PROTOCOL_VERSION)
        negotiated_version = (
            protocol_version
            if protocol_version in SUPPORTED_PROTOCOL_VERSIONS
            else DEFAULT_PROTOCOL_VERSION
        )
        return _jsonrpc_result(
            message_id,
            {
                "protocolVersion": negotiated_version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": SERVER_INFO,
                "instructions": (
                    "Signal Graph MCP exposes CLI-equivalent journal capture, journalize, "
                    "and recall tools with provenance-rich outputs."
                ),
            },
        )
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return _jsonrpc_result(message_id, {})
    if method == "tools/list":
        return _jsonrpc_result(message_id, {"tools": build_tool_definitions()})
    if method == "tools/call":
        try:
            result = _handle_tool_call(
                params,
                store=store,
                artifact_dir=artifact_dir or DEFAULT_PROJECT_DIR / "artifacts",
            )
        except ValueError as exc:
            return _jsonrpc_result(
                message_id,
                {"content": [{"type": "text", "text": str(exc)}], "isError": True},
            )
        except Exception as exc:  # noqa: BLE001
            return _jsonrpc_error(message_id, -32603, f"Server error: {exc}")
        return _jsonrpc_result(message_id, result)
    return _jsonrpc_error(message_id, -32601, f"Method not found: {method}")


def serve_stdio(
    *,
    store_path: Path | None = None,
    artifact_dir: Path | None = None,
) -> None:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            response = _jsonrpc_error(None, -32700, f"Parse error: {exc}")
        else:
            response = handle_message(
                message,
                store_path=store_path,
                artifact_dir=artifact_dir,
            )
        if response is None:
            continue
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


def main() -> None:
    store = SqliteStore(DEFAULT_PROJECT_DIR / "signal_graph.db")
    store.init_db()
    serve_stdio()


def _handle_tool_call(
    params: dict[str, Any],
    *,
    store: SqliteStore,
    artifact_dir: Path,
) -> dict[str, Any]:
    name = params.get("name")
    arguments = params.get("arguments") or {}
    if name == "signal_graph_capture_signal":
        store.init_db()
        signal = create_journal_signal(
            text=str(arguments["text"]),
            origin_type=parse_origin_type(str(arguments["origin_type"])),
            source_name=str(arguments["source_name"]),
            source_url=_optional_str(arguments.get("source_url")),
            source_ref=_optional_str(arguments.get("source_ref")),
            raw_payload=_optional_str(arguments.get("raw_payload")),
            observed_at=parse_optional_datetime(_optional_str(arguments.get("observed_at"))),
            published_at=parse_optional_datetime(_optional_str(arguments.get("published_at"))),
            agent_host=_optional_str(arguments.get("host")),
            agent_process=_optional_str(arguments.get("process")),
            agent_runtime=_optional_str(arguments.get("runtime_family")),
            agent_session_id=_optional_str(arguments.get("session_id")),
            agent_role=_optional_str(arguments.get("role")),
            workspace_path=_optional_str(arguments.get("workspace_path")),
            intent_status=parse_intent_status(
                str(arguments.get("intent_status") or "unknown")
            ),
            why_text=_optional_str(arguments.get("why")),
            who_refs=_string_list(arguments.get("who")),
            what_refs=_string_list(arguments.get("what")),
            where_refs=_string_list(arguments.get("where")),
            how_refs=_string_list(arguments.get("how")),
        )
        store.save_journal_signal(signal)
        return _tool_success(
            text=f"Captured signal {signal.signal_id}",
            structured_content=signal.model_dump(mode="json"),
        )
    if name == "signal_graph_journalize_signal":
        store.init_db()
        journaled = journalize_signal(store, str(arguments["signal_id"]))
        return _tool_success(
            text=f"Journalized signal {journaled.signal_id}",
            structured_content=journaled.model_dump(mode="json"),
        )
    if name == "signal_graph_recall_signal":
        store.init_db()
        artifact = recall_signals(
            store,
            query=str(arguments["query"]),
            artifact_dir=artifact_dir,
            limit=int(arguments.get("limit", 5)),
            origin_type=_optional_str(arguments.get("origin_type")),
            session_id=_optional_str(arguments.get("session_id")),
            runtime_family=_optional_str(arguments.get("runtime_family")),
            source_name=_optional_str(arguments.get("source_name")),
        )
        return _tool_success(
            text=artifact.markdown_text,
            structured_content=artifact.model_dump(mode="json"),
        )
    if name == "signal_graph_list_signals":
        store.init_db()
        signals = store.search_journal_signals(
            query=_optional_str(arguments.get("query")) or "",
            limit=int(arguments.get("limit", 10)),
            origin_type=_optional_str(arguments.get("origin_type")),
            session_id=_optional_str(arguments.get("session_id")),
            runtime_family=_optional_str(arguments.get("runtime_family")),
            source_name=_optional_str(arguments.get("source_name")),
        )
        return _tool_success(
            text=f"Matched {len(signals)} journal signals",
            structured_content={
                "signals": [signal.model_dump(mode="json") for signal in signals]
            },
        )
    return _jsonrpc_error_result(f"Unknown tool: {name}")


def _jsonrpc_result(message_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def _jsonrpc_error(message_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": message_id,
        "error": {"code": code, "message": message},
    }


def _jsonrpc_error_result(message: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": message}], "isError": True}


def _tool_success(
    *,
    text: str,
    structured_content: dict[str, Any],
) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": text}],
        "structuredContent": structured_content,
        "isError": False,
    }


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]
