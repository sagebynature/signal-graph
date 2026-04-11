from __future__ import annotations

from datetime import UTC, datetime

from signal_graph.models.journal import JournalSignal
from signal_graph.services.recall_engine import build_recall_query, run_recall_query


def _signal(
    signal_id: str,
    text: str,
    *,
    session_id: str | None = None,
    observed_at: datetime | None = None,
) -> JournalSignal:
    return JournalSignal(
        signal_id=signal_id,
        origin_type="user",
        source_name="manual",
        raw_text=text,
        content_hash=f"hash-{signal_id}",
        captured_at=observed_at or datetime.now(UTC),
        observed_at=observed_at,
        agent_session_id=session_id,
        what_refs=["deployment"],
    )


def test_build_recall_query_parses_exact_phrases_and_tokens():
    query = build_recall_query(
        query='"deployment checklist" approval',
        limit=5,
        view="ranked",
    )

    assert query.exact_phrases == ["deployment checklist"]
    assert query.tokens == ["approval"]


def test_build_recall_query_rejects_unmatched_quotes():
    try:
        build_recall_query(query='"deployment checklist', limit=5, view="ranked")
    except ValueError as exc:
        assert "unmatched double quote" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected unmatched quote error")


def test_run_recall_query_prefers_exact_phrase_match():
    signals = [
        _signal("sig-exact", "Agent completed the deployment checklist for release."),
        _signal("sig-loose", "Agent completed the deployment and later reviewed the checklist."),
    ]
    query = build_recall_query(
        query='"deployment checklist"',
        limit=5,
        view="ranked",
    )

    result = run_recall_query(signals=signals, query=query)

    assert result.matches[0].signal.signal_id == "sig-exact"
    assert result.matches[0].explanation.phrase_hits == ["deployment checklist"]


def test_run_recall_query_session_view_groups_and_orders_latest_session_first():
    signals = [
        _signal(
            "sig-old",
            "Deployment signal in older session.",
            session_id="session-old",
            observed_at=datetime(2026, 4, 10, 9, 0, tzinfo=UTC),
        ),
        _signal(
            "sig-new",
            "Deployment signal in newer session.",
            session_id="session-new",
            observed_at=datetime(2026, 4, 11, 9, 0, tzinfo=UTC),
        ),
    ]
    query = build_recall_query(query="deployment", limit=5, view="session")

    result = run_recall_query(signals=signals, query=query)

    assert [group.session_key for group in result.session_groups] == [
        "session-new",
        "session-old",
    ]
    assert result.matches[0].signal.signal_id == "sig-new"
