from __future__ import annotations

from datetime import UTC, datetime

from signal_graph.memory_v2 import CapturePolicy, FileMemoryStore, MemoryService
from signal_graph.memory_v2.mcp import handle_http_request, handle_stdio_message


def _service(tmp_path):
    service = MemoryService(
        store=FileMemoryStore(tmp_path / "memory-v2"),
        policy=CapturePolicy(),
    )
    service.create_owner(email="sage@example.com", display_name="Sage")
    actor = service.register_actor(
        owner_email="sage@example.com",
        runtime_family="codex",
        host="machine-a",
        session_id="session-1",
    )
    decision = service.capture_hook_event(
        owner_email="sage@example.com",
        actor_id=actor.actor_id,
        phase="post_output",
        action_text="Selected approach-x",
        observed_facts=["updated the implementation note"],
        topic_refs=["approach-x"],
        occurred_at=datetime(2026, 4, 12, 13, 0, tzinfo=UTC),
        inferred_why="Approach-x preserves provenance.",
        why_confidence=0.82,
        confirmed=True,
        evidence_refs=["notes/decision.md"],
    )
    return service, decision.event_id


def test_stdio_and_http_transports_have_capability_parity(tmp_path):
    service, decision_event_id = _service(tmp_path)

    initialize = handle_stdio_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-03-26"},
        },
        service=service,
    )
    assert initialize["result"]["protocolVersion"] == "2025-03-26"

    tools = handle_stdio_message(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        service=service,
    )
    tool_names = {tool["name"] for tool in tools["result"]["tools"]}
    assert {"memory_query", "memory_explain", "memory_correct"} <= tool_names

    stdio_query = handle_stdio_message(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "memory_query",
                "arguments": {
                    "owner_email": "sage@example.com",
                    "topic": "approach-x",
                },
            },
        },
        service=service,
    )
    http_query = handle_http_request(
        "POST",
        "/tools/memory_query",
        {"owner_email": "sage@example.com", "topic": "approach-x"},
        service=service,
    )
    assert stdio_query["result"]["structuredContent"] == http_query["body"]

    stdio_explain = handle_stdio_message(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "memory_explain",
                "arguments": {"event_id": decision_event_id},
            },
        },
        service=service,
    )
    http_explain = handle_http_request(
        "POST",
        "/tools/memory_explain",
        {"event_id": decision_event_id},
        owner_email="sage@example.com",
        service=service,
    )
    assert stdio_explain["result"]["structuredContent"] == http_explain["body"]

    stdio_correct = handle_stdio_message(
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "memory_correct",
                "arguments": {
                    "owner_email": "sage@example.com",
                    "target_id": decision_event_id,
                    "topic": "approach-x",
                    "instruction": "Do not choose approach-x by default.",
                },
            },
        },
        service=service,
    )
    http_correct = handle_http_request(
        "POST",
        "/tools/memory_correct",
        {
            "owner_email": "sage@example.com",
            "target_id": decision_event_id,
            "topic": "approach-x",
            "instruction": "Do not choose approach-x by default.",
        },
        owner_email="sage@example.com",
        service=service,
    )
    assert stdio_correct["result"]["structuredContent"] == http_correct["body"]


def test_http_boundary_requires_owner_scope_and_blocks_mismatches(tmp_path):
    service, decision_event_id = _service(tmp_path)

    missing_scope = handle_http_request(
        "POST",
        "/tools/memory_explain",
        {"event_id": decision_event_id},
        service=service,
    )
    assert missing_scope == {
        "status": 400,
        "body": {"error": "owner_scope_required"},
    }

    mismatched_scope = handle_http_request(
        "POST",
        "/tools/memory_query",
        {"owner_email": "sage@example.com", "topic": "approach-x"},
        owner_email="other@example.com",
        service=service,
    )
    assert mismatched_scope == {
        "status": 403,
        "body": {"error": "owner_scope_mismatch"},
    }

    explain = handle_http_request(
        "POST",
        "/tools/memory_explain",
        {"event_id": decision_event_id},
        owner_email="sage@example.com",
        service=service,
    )
    assert explain["status"] == 200
    assert explain["body"]["owner"]["email"] == "sage@example.com"
