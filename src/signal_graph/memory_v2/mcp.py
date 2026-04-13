from __future__ import annotations

from typing import Any

from signal_graph.memory_v2.service import MemoryService


def build_tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "memory_query",
            "description": "Query owner-scoped memory by topic and optional date.",
        },
        {
            "name": "memory_explain",
            "description": "Explain a prior action with provenance and active guidance.",
        },
        {
            "name": "memory_correct",
            "description": "Record a correction/redaction-style instruction.",
        },
        {
            "name": "memory_redact",
            "description": "Redact a target from query and explanation results.",
        },
    ]


def handle_stdio_message(
    message: dict[str, Any], *, service: MemoryService
) -> dict[str, Any]:
    method = message["method"]
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": message["id"],
            "result": {
                "protocolVersion": message["params"]["protocolVersion"],
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "signal-graph-memory-v2", "version": "0.1.0"},
            },
        }
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": message["id"],
            "result": {"tools": build_tool_definitions()},
        }
    if method != "tools/call":
        raise ValueError(f"unsupported stdio method: {method}")

    tool_name = message["params"]["name"]
    arguments = message["params"].get("arguments", {})
    payload = _dispatch_tool(tool_name, arguments, service)
    return {
        "jsonrpc": "2.0",
        "id": message["id"],
        "result": {
            "content": [{"type": "text", "text": f"{tool_name} ok"}],
            "isError": False,
            "structuredContent": payload,
        },
    }


def handle_http_request(
    method: str,
    path: str,
    body: dict[str, Any],
    *,
    owner_email: str | None = None,
    service: MemoryService,
) -> dict[str, Any]:
    if method != "POST":
        return {"status": 405, "body": {"error": "method_not_allowed"}}
    scope_owner = owner_email or body.get("owner_email")
    if scope_owner is None:
        return {"status": 400, "body": {"error": "owner_scope_required"}}
    if "owner_email" in body and body["owner_email"] != scope_owner:
        return {"status": 403, "body": {"error": "owner_scope_mismatch"}}
    tool_name = path.removeprefix("/tools/")
    arguments = dict(body)
    if tool_name in {
        "memory_query",
        "memory_explain",
        "memory_correct",
        "memory_redact",
    }:
        arguments["owner_email"] = scope_owner
    return {"status": 200, "body": _dispatch_tool(tool_name, arguments, service)}


def _dispatch_tool(
    tool_name: str,
    arguments: dict[str, Any],
    service: MemoryService,
) -> dict[str, Any]:
    if tool_name == "memory_query":
        result = service.query(**arguments)
    elif tool_name == "memory_explain":
        if "owner_email" in arguments:
            result = service.explain_action_for_owner(**arguments)
        else:
            result = service.explain_action(**arguments)
    elif tool_name == "memory_correct":
        result = service.record_correction(**arguments)
    elif tool_name == "memory_redact":
        result = service.record_redaction(**arguments)
    else:
        raise ValueError(f"unknown tool: {tool_name}")
    return result.model_dump(mode="json")
