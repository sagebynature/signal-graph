from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

TimingWindow = Literal["immediate", "short_drift"]


class PathPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationship_path: tuple[str, ...]
    description: str = Field(min_length=1)
    base_score: float = Field(ge=0.0, le=1.0)
    timing_window: TimingWindow = "short_drift"

    @model_validator(mode="after")
    def validate_relationship_path(self) -> PathPolicy:
        if not self.relationship_path:
            raise ValueError("relationship_path must not be empty")
        return self


class EventPolicyOverride(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationship_path: tuple[str, ...]
    base_score: float | None = Field(default=None, ge=0.0, le=1.0)
    timing_window: TimingWindow | None = None
    rationale: str | None = None

    @model_validator(mode="after")
    def validate_relationship_path(self) -> EventPolicyOverride:
        if not self.relationship_path:
            raise ValueError("relationship_path must not be empty")
        return self


class EventPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: str = Field(min_length=1)
    direction: str = Field(min_length=1)
    overrides: list[EventPolicyOverride] = Field(default_factory=list)
    fallback_rationale: str | None = None


class ResolvedPathPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationship_path: tuple[str, ...]
    description: str
    base_score: float
    timing_window: TimingWindow
    rationale: str | None = None


class ScoringPolicy(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    path_policies: list[PathPolicy] = Field(default_factory=list, alias="paths")
    event_policies: list[EventPolicy] = Field(default_factory=list, alias="events")

    def merged_with(self, override: ScoringPolicy) -> ScoringPolicy:
        path_policies = list(self.path_policies)
        for path_policy in override.path_policies:
            existing_index = next(
                (
                    index
                    for index, existing in enumerate(path_policies)
                    if existing.relationship_path == path_policy.relationship_path
                ),
                None,
            )
            if existing_index is None:
                path_policies.append(path_policy)
            else:
                path_policies[existing_index] = path_policy

        event_policies = list(self.event_policies)
        for event_policy in override.event_policies:
            existing_index = next(
                (
                    index
                    for index, existing in enumerate(event_policies)
                    if (
                        existing.event_type == event_policy.event_type
                        and existing.direction == event_policy.direction
                    )
                ),
                None,
            )
            if existing_index is None:
                event_policies.append(event_policy)
                continue

            existing = event_policies[existing_index]
            merged_overrides = list(existing.overrides)
            for override_policy in event_policy.overrides:
                override_index = next(
                    (
                        index
                        for index, existing_override in enumerate(merged_overrides)
                        if (
                            existing_override.relationship_path
                            == override_policy.relationship_path
                        )
                    ),
                    None,
                )
                if override_index is None:
                    merged_overrides.append(override_policy)
                else:
                    merged_overrides[override_index] = override_policy

            event_policies[existing_index] = EventPolicy(
                event_type=existing.event_type,
                direction=existing.direction,
                overrides=merged_overrides,
                fallback_rationale=(
                    event_policy.fallback_rationale
                    if event_policy.fallback_rationale is not None
                    else existing.fallback_rationale
                ),
            )

        return ScoringPolicy(paths=path_policies, events=event_policies)

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
