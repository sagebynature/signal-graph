from __future__ import annotations

from datetime import datetime
import re
from typing import cast

from signal_graph.models.journal import (
    JournalSignal,
    OriginType,
    RECALL_ORDERING_PRECEDENCE,
    RecallMatch,
    RecallMatchExplanation,
    RecallQuery,
    RecallResult,
    RecallSessionGroup,
    RecallView,
)

_TOKEN_PATTERN = re.compile(r"[a-z0-9_:-]+")


def build_recall_query(
    *,
    query: str,
    limit: int,
    origin_type: str | None = None,
    session_id: str | None = None,
    runtime_family: str | None = None,
    source_name: str | None = None,
    view: str = "ranked",
) -> RecallQuery:
    normalized_query = query.strip()
    phrases = _parse_exact_phrases(normalized_query)
    token_text = _strip_exact_phrases(normalized_query)
    tokens = _TOKEN_PATTERN.findall(token_text.lower())
    normalized_view = _parse_view(view)

    if not normalized_query and not any(
        [origin_type, session_id, runtime_family, source_name]
    ):
        raise ValueError("recall query must be non-empty unless filters are provided")

    return RecallQuery(
        raw_query=normalized_query,
        tokens=tokens,
        exact_phrases=phrases,
        origin_type=_parse_origin_type(origin_type),
        session_id=session_id,
        runtime_family=runtime_family,
        source_name=source_name,
        view=normalized_view,
        limit=limit,
    )


def run_recall_query(
    *,
    signals: list[JournalSignal],
    query: RecallQuery,
) -> RecallResult:
    filtered = _filter_signals(signals, query)
    matches = _rank_matches(filtered, query)
    ordered_matches, session_groups = _order_matches(matches, query.view)
    limited_matches = ordered_matches[: query.limit]
    if query.view == "session":
        session_groups = _trim_session_groups(session_groups, limited_matches)
    else:
        session_groups = []
    return RecallResult(
        view=query.view,
        query_contract=query,
        ordering_precedence=RECALL_ORDERING_PRECEDENCE[query.view],
        matches=limited_matches,
        session_groups=session_groups,
    )


def render_richer_recall_markdown(result: RecallResult) -> str:
    matches = result.matches
    origin_types = sorted({match.signal.origin_type for match in matches})
    sessions = sorted(
        {
            match.signal.agent_session_id
            for match in matches
            if match.signal.agent_session_id is not None
        }
    )
    lines = [
        "# Signal Recall",
        "",
        f"- Query: `{result.query_contract.raw_query or 'none (filter-only recall)'}`",
        f"- View: `{result.view}`",
        f"- Matched signals: {len(matches)}",
        f"- Origin types: {', '.join(origin_types) if origin_types else 'none'}",
        f"- Sessions: {', '.join(sessions) if sessions else 'none recorded'}",
        _filters_markdown_line(result.query_contract),
        f"- Ordering: `{', '.join(result.ordering_precedence)}`",
        "",
        "## Summary",
        (
            "Signal Graph matched signals with provenance-rich recall. "
            "Every entry below preserves raw signal context plus origin, session, "
            "location, graph path, intent status, and explicit ranking explanation."
        ),
    ]
    if result.view == "session" and result.session_groups:
        lines.extend(["", "## Session Groups"])
        for group in result.session_groups:
            lines.extend(
                [
                    "",
                    f"### Session `{group.session_key}`",
                    (
                        f"- Latest timestamp: `{group.latest_timestamp.isoformat()}`"
                        if group.latest_timestamp
                        else "- Latest timestamp: `unknown`"
                    ),
                    f"- Signals: {', '.join(group.signal_ids)}",
                ]
            )
    lines.extend(["", "## Matches"])

    for match in matches:
        signal = match.signal
        explanation = match.explanation
        lines.extend(
            [
                "",
                f"### {signal.signal_id}",
                f"- Score: `{match.score:.2f}`",
                f"- Origin: `{signal.origin_type}` via `{signal.source_name}`",
                f"- Captured at: `{_isoformat(_signal_sort_timestamp(signal)) or 'unknown'}`",
                (
                    "- Agent/session: "
                    f"`{signal.agent_runtime or 'human'}` / "
                    f"`{signal.agent_process or 'n/a'}` / "
                    f"`{signal.agent_session_id or 'n/a'}`"
                ),
                f"- Source ref: `{signal.source_ref or signal.source_url or signal.workspace_path or 'none recorded'}`",
                f"- Graph path: `{' -> '.join(signal.graph_path) or 'none recorded'}`",
                f"- Intent: `{signal.intent_status}` — {signal.why_text or 'why not asserted'}",
                "",
                "#### Why this matched",
                f"- Matched fields: {', '.join(explanation.matched_fields) or 'none'}",
                f"- Phrase hits: {', '.join(explanation.phrase_hits) or 'none'}",
                (
                    "- Filter matches: "
                    + ", ".join(
                        f"{key}={value}"
                        for key, value in explanation.filter_matches.items()
                    )
                    if explanation.filter_matches
                    else "- Filter matches: none"
                ),
                (
                    "- Score components: "
                    + ", ".join(
                        f"{key}={value:.2f}"
                        for key, value in explanation.score_components.items()
                        if value > 0
                    )
                    if any(value > 0 for value in explanation.score_components.values())
                    else "- Score components: none"
                ),
                f"- Graph-path contribution: {', '.join(explanation.graph_path_labels) or 'none'}",
                f"- Intent-status note: {explanation.intent_status_note}",
                "",
                "```text",
                signal.raw_text,
                "```",
            ]
        )
    return "\n".join(lines)


def _filter_signals(signals: list[JournalSignal], query: RecallQuery) -> list[JournalSignal]:
    filtered: list[JournalSignal] = []
    for signal in signals:
        if query.origin_type is not None and signal.origin_type != query.origin_type:
            continue
        if query.session_id is not None and signal.agent_session_id != query.session_id:
            continue
        if query.runtime_family is not None and signal.agent_runtime != query.runtime_family:
            continue
        if query.source_name is not None and signal.source_name != query.source_name:
            continue
        filtered.append(signal)
    return filtered


def _rank_matches(signals: list[JournalSignal], query: RecallQuery) -> list[RecallMatch]:
    matches: list[RecallMatch] = []
    for signal in signals:
        match = _score_signal(signal, query)
        if match is None:
            continue
        matches.append(match)
    return matches


def _score_signal(signal: JournalSignal, query: RecallQuery) -> RecallMatch | None:
    raw_text = signal.raw_text.lower()
    source_values = {
        "source_name": (signal.source_name or "").lower(),
        "source_ref": (signal.source_ref or "").lower(),
        "source_url": (signal.source_url or "").lower(),
        "workspace_path": (signal.workspace_path or "").lower(),
        "origin_type": signal.origin_type.lower(),
        "runtime_family": (signal.agent_runtime or "").lower(),
        "session_id": (signal.agent_session_id or "").lower(),
    }
    taxonomy = {
        "who": [ref.lower() for ref in signal.who_refs],
        "what": [ref.lower() for ref in signal.what_refs],
        "where": [ref.lower() for ref in signal.where_refs],
        "how": [ref.lower() for ref in signal.how_refs],
        "why": [(signal.why_text or "").lower()],
    }
    matched_fields: list[str] = []
    phrase_hits: list[str] = []
    score_components = {
        "phrase": 0.0,
        "raw_text": 0.0,
        "taxonomy": 0.0,
        "source": 0.0,
        "filter": 0.0,
        "graph_path": 0.0,
        "intent_status": 0.0,
    }

    for phrase in query.exact_phrases:
        if phrase in raw_text:
            score_components["phrase"] += 12.0
            phrase_hits.append(phrase)
            matched_fields.append("raw_text_phrase")
        elif any(phrase in value for value in source_values.values()):
            score_components["phrase"] += 8.0
            phrase_hits.append(phrase)
            matched_fields.append("source_phrase")

    for token in query.tokens:
        if token in raw_text:
            score_components["raw_text"] += 5.0
            matched_fields.append("raw_text")
        if any(token in value for value in taxonomy["what"]):
            score_components["taxonomy"] += 4.0
            matched_fields.append("what")
        if any(token in value for value in source_values.values()):
            score_components["source"] += 3.0
            matched_fields.append("source")
        if any(
            token in value
            for field in ("who", "where", "how", "why")
            for value in taxonomy[field]
        ):
            score_components["taxonomy"] += 2.0
            matched_fields.append("context")
        if any(token in label.lower() for label in signal.graph_path):
            score_components["graph_path"] += 1.0
            matched_fields.append("graph_path")

    filter_matches = {
        key: value
        for key, value in {
            "origin_type": query.origin_type,
            "session_id": query.session_id,
            "runtime_family": query.runtime_family,
            "source_name": query.source_name,
        }.items()
        if value is not None
    }
    score_components["filter"] = float(len(filter_matches))
    score_components["graph_path"] += 0.5 if signal.graph_path else 0.0
    score_components["intent_status"] = {"explicit": 0.5, "inferred": 0.25}.get(
        signal.intent_status, 0.0
    )

    total_score = sum(score_components.values())
    if query.raw_query and total_score <= 0:
        return None

    explanation = RecallMatchExplanation(
        matched_fields=sorted(set(matched_fields)),
        phrase_hits=phrase_hits,
        filter_matches={key: value for key, value in filter_matches.items()},
        score_components=score_components,
        graph_path_labels=signal.graph_path,
        intent_status_note=(
            "Intent is explicit."
            if signal.intent_status == "explicit"
            else "Intent is inferred."
            if signal.intent_status == "inferred"
            else "Intent is unknown or intentionally omitted."
        ),
    )
    return RecallMatch(signal=signal, score=total_score, explanation=explanation)


def _order_matches(
    matches: list[RecallMatch], view: RecallView
) -> tuple[list[RecallMatch], list[RecallSessionGroup]]:
    if view == "timeline":
        ordered = sorted(
            matches,
            key=lambda match: (
                _sortable_timestamp(match.signal),
                match.score,
                _stable_signal_id(match.signal.signal_id),
            ),
            reverse=True,
        )
        return ordered, []
    if view == "session":
        groups = _build_session_groups(matches)
        ordered_matches = [match for group in groups for match in group.matches]
        return ordered_matches, groups

    ordered = sorted(
        matches,
        key=lambda match: (
            match.score,
            _sortable_timestamp(match.signal),
            _stable_signal_id(match.signal.signal_id),
        ),
        reverse=True,
    )
    return ordered, []


def _build_session_groups(matches: list[RecallMatch]) -> list[RecallSessionGroup]:
    grouped: dict[str, list[RecallMatch]] = {}
    for match in matches:
        session_key = match.signal.agent_session_id or "no-session"
        grouped.setdefault(session_key, []).append(match)

    session_groups: list[RecallSessionGroup] = []
    for session_key, session_matches in grouped.items():
        ordered_matches = sorted(
            session_matches,
            key=lambda match: (
                match.score,
                _sortable_timestamp(match.signal),
                _stable_signal_id(match.signal.signal_id),
            ),
            reverse=True,
        )
        latest_timestamp = max(
            (_signal_sort_timestamp(match.signal) for match in ordered_matches),
            default=None,
        )
        session_groups.append(
            RecallSessionGroup(
                session_key=session_key,
                latest_timestamp=latest_timestamp,
                signal_ids=[match.signal.signal_id for match in ordered_matches],
                matches=ordered_matches,
            )
        )

    return sorted(
        session_groups,
        key=lambda group: (
            _sortable_datetime(group.latest_timestamp),
            group.session_key,
        ),
        reverse=True,
    )


def _trim_session_groups(
    groups: list[RecallSessionGroup], limited_matches: list[RecallMatch]
) -> list[RecallSessionGroup]:
    allowed_ids = {match.signal.signal_id for match in limited_matches}
    trimmed_groups: list[RecallSessionGroup] = []
    for group in groups:
        group_matches = [
            match for match in group.matches if match.signal.signal_id in allowed_ids
        ]
        if not group_matches:
            continue
        trimmed_groups.append(
            RecallSessionGroup(
                session_key=group.session_key,
                latest_timestamp=max(
                    (_signal_sort_timestamp(match.signal) for match in group_matches),
                    default=None,
                ),
                signal_ids=[match.signal.signal_id for match in group_matches],
                matches=group_matches,
            )
        )
    return trimmed_groups


def _parse_exact_phrases(query: str) -> list[str]:
    if query.count('"') % 2 != 0:
        raise ValueError('recall query contains an unmatched double quote')
    phrases = [phrase.strip().lower() for phrase in re.findall(r'"([^"]+)"', query)]
    if any(not phrase for phrase in phrases):
        raise ValueError("exact phrases must contain non-empty text")
    return phrases


def _parse_view(value: str) -> RecallView:
    normalized = value.strip().lower()
    valid = {"ranked", "timeline", "session"}
    if normalized not in valid:
        raise ValueError("view must be one of: ranked, timeline, session")
    return cast(RecallView, normalized)


def _parse_origin_type(value: str | None) -> OriginType | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    valid = {"user", "agent_artifact", "external_reference"}
    if normalized not in valid:
        raise ValueError(
            "origin_type must be one of: user, agent_artifact, external_reference"
        )
    return cast(OriginType, normalized)


def _strip_exact_phrases(query: str) -> str:
    return re.sub(r'"[^"]+"', " ", query)


def _filters_markdown_line(query: RecallQuery) -> str:
    rendered = [
        f"{key}={value}"
        for key, value in {
            "origin_type": query.origin_type,
            "session_id": query.session_id,
            "runtime_family": query.runtime_family,
            "source_name": query.source_name,
        }.items()
        if value is not None
    ]
    return f"- Filters: {', '.join(rendered)}" if rendered else "- Filters: none"


def _sortable_timestamp(signal: JournalSignal) -> tuple[int, str, str]:
    timestamp = _signal_sort_timestamp(signal)
    return (
        1 if timestamp is not None else 0,
        timestamp.isoformat() if timestamp else "",
        _stable_signal_id(signal.signal_id),
    )


def _sortable_datetime(value: datetime | None) -> tuple[int, str]:
    return (1 if value is not None else 0, value.isoformat() if value else "")


def _signal_sort_timestamp(signal: JournalSignal) -> datetime | None:
    return signal.observed_at or signal.captured_at or signal.published_at


def _stable_signal_id(signal_id: str) -> str:
    return signal_id


def _isoformat(value: datetime | None) -> str | None:
    return value.isoformat() if value else None
