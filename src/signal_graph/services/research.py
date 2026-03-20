from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from signal_graph.models.events import EventCandidate
from signal_graph.models.research import ResearchBundle, ResearchBundleInput
from signal_graph.storage.sqlite import SqliteStore


def load_research_bundle_input(bundle_file: Path | None) -> ResearchBundleInput:
    if bundle_file is None:
        return ResearchBundleInput()

    try:
        return ResearchBundleInput.model_validate(json.loads(bundle_file.read_text()))
    except FileNotFoundError as exc:
        raise ValueError(f"research bundle file not found: {bundle_file}") from exc
    except OSError as exc:
        raise ValueError(f"unable to read research bundle file: {bundle_file}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"research bundle file is not valid JSON: {bundle_file}"
        ) from exc
    except ValidationError as exc:
        raise ValueError(f"research bundle file is invalid: {exc}") from exc


def build_research_bundle(
    event: EventCandidate,
    bundle_input: ResearchBundleInput,
) -> ResearchBundle:
    return ResearchBundle(
        research_bundle_id=f"rb-{event.event_candidate_id}",
        event_candidate_id=event.event_candidate_id,
        supporting_documents=bundle_input.supporting_documents,
        contradictions=bundle_input.contradictions,
        entity_resolution_results=bundle_input.entity_resolution_results,
        evidence_spans=bundle_input.evidence_spans,
        research_confidence=bundle_input.research_confidence,
        research_notes=bundle_input.research_notes,
    )


def build_and_persist_research_bundle(
    store: SqliteStore,
    event_candidate_id: str,
    *,
    bundle_input: ResearchBundleInput | None = None,
    allow_empty: bool = False,
) -> ResearchBundle:
    event_candidate = store.get_event_candidate(event_candidate_id)
    if event_candidate is None:
        raise ValueError(f"event candidate not found: {event_candidate_id}")

    materialized_bundle = bundle_input or ResearchBundleInput()
    if materialized_bundle.is_empty() and not allow_empty:
        raise ValueError("empty research bundle requires --allow-empty")

    bundle = build_research_bundle(event_candidate, materialized_bundle)
    store.save_research_bundle(bundle)
    return bundle
