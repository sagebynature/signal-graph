from __future__ import annotations

from pydantic import BaseModel, Field


class PathPolicy(BaseModel):
    relationship_path: tuple[str, ...]
    description: str
    base_score: float
    timing_window: str = "short_drift"


class EventPolicyOverride(BaseModel):
    relationship_path: tuple[str, ...]
    base_score: float | None = None
    timing_window: str | None = None
    rationale: str | None = None


class EventPolicy(BaseModel):
    event_type: str
    direction: str
    overrides: list[EventPolicyOverride] = Field(default_factory=list)
    fallback_rationale: str | None = None


class ResolvedPathPolicy(BaseModel):
    relationship_path: tuple[str, ...]
    description: str
    base_score: float
    timing_window: str
    rationale: str | None = None


class ScoringPolicy(BaseModel):
    path_policies: list[PathPolicy] = Field(default_factory=list)
    event_policies: list[EventPolicy] = Field(default_factory=list)

    def resolve(
        self, relationship_path: list[str], *, event_type: str = "", direction: str = ""
    ) -> ResolvedPathPolicy:
        path_key = tuple(relationship_path)
        path_policy = next(
            (
                policy
                for policy in self.path_policies
                if policy.relationship_path == path_key
            ),
            None,
        )
        if path_policy is None:
            path_policy = PathPolicy(
                relationship_path=path_key,
                description="graph relationship exposure",
                base_score=0.32,
                timing_window="short_drift",
            )

        event_policy = next(
            (
                policy
                for policy in self.event_policies
                if policy.event_type == event_type and policy.direction == direction
            ),
            None,
        )
        override = (
            next(
                (
                    candidate
                    for candidate in event_policy.overrides
                    if candidate.relationship_path == path_key
                ),
                None,
            )
            if event_policy is not None
            else None
        )

        return ResolvedPathPolicy(
            relationship_path=path_key,
            description=path_policy.description,
            base_score=(
                override.base_score
                if override is not None and override.base_score is not None
                else path_policy.base_score
            ),
            timing_window=(
                override.timing_window
                if override is not None and override.timing_window is not None
                else path_policy.timing_window
            ),
            rationale=(
                override.rationale
                if override is not None and override.rationale is not None
                else event_policy.fallback_rationale
                if event_policy is not None
                else None
            ),
        )
