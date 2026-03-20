# Scoring Policy Config Design

## Goal

Make scoring policy externally configurable so operators can tune ranking, timing, and memo rationale without editing Python code.

This change must preserve three properties:

- built-in defaults continue to work with zero local setup
- a local project config can override specific policy rules safely
- docs include copyable examples that match the real parser and merge behavior

## Scope

This design covers:

- loading scoring-policy overrides from `.signal-graph/config.toml`
- keeping a checked-in example policy file in the repo
- merging local overrides onto the built-in default policy
- validating policy config strictly and failing fast on malformed input
- documenting precedence, examples, and operator workflow

This design does not cover:

- hot reloading policy while a long-running process is active
- remote policy distribution
- multiple policy profiles selected at runtime

## User-Facing Behavior

`Signal Graph` will continue to ship with a built-in scoring policy. If `.signal-graph/config.toml` does not define a scoring policy section, the system behaves exactly as it does today.

If `.signal-graph/config.toml` includes a `[scoring_policy]` section, local values override the built-in policy by exact match:

- path policy match key: `relationship_path`
- event override match key: `event_type + direction + relationship_path`
- event fallback rationale match key: `event_type + direction`

The effective policy is used by:

- ranking score calculation
- timing classification
- memo explanation and rationale text

## Config Shape

The local project config remains `.signal-graph/config.toml`.

Example shape:

```toml
[neo4j]
uri = "neo4j://localhost:7687"
username = "neo4j"
password = "password"
database = "neo4j"

[scoring_policy]

[[scoring_policy.paths]]
relationship_path = ["DIRECT_ENTITY"]
description = "direct company exposure"
base_score = 0.70
timing_window = "immediate"

[[scoring_policy.paths]]
relationship_path = ["HOLDS"]
description = "ETF holding exposure"
base_score = 0.50
timing_window = "immediate"

[[scoring_policy.paths]]
relationship_path = ["SUPPLIES_TO_AFFECTED"]
description = "upstream supplier exposure"
base_score = 0.44
timing_window = "short_drift"

[[scoring_policy.events]]
event_type = "capex_cut"
direction = "negative"
fallback_rationale = "For a negative `capex_cut`, direct company and closely linked holdings are the default immediate read-through."

[[scoring_policy.events.overrides]]
relationship_path = ["SUPPLIES_TO_AFFECTED"]
base_score = 0.62
timing_window = "immediate"
rationale = "For a negative `capex_cut`, upstream suppliers can react quickly because lower spending often hits equipment and input demand first."

[[scoring_policy.events.overrides]]
relationship_path = ["SUPPLIES_TO_CUSTOMER"]
base_score = 0.34
timing_window = "short_drift"
rationale = "For a negative `capex_cut`, downstream customers are usually a second-order effect."
```

## Merge Rules

The loader builds the effective policy in two stages:

1. Start with the current built-in `ScoringPolicy`.
2. Apply local overrides from `.signal-graph/config.toml`.

Merge behavior:

- If a local `paths` entry matches an existing `relationship_path`, replace the built-in values for that path.
- If a local `paths` entry uses a new `relationship_path`, append it as a new path policy.
- If a local `events` entry matches an existing `event_type + direction`, merge its fallback rationale and overrides into that event policy.
- If a local event override matches an existing `relationship_path`, replace that override.
- If a local event override introduces a new `relationship_path`, append it.
- If a local `events` entry introduces a new `event_type + direction`, append it as a new event policy.

This gives operators additive customization without forcing them to duplicate the full built-in policy.

## Validation

Policy config should fail fast with a clear error when malformed.

Validation rules:

- `relationship_path` must be a non-empty list of strings
- `description` must be non-empty for path policies
- `base_score` must be between `0.0` and `1.0`
- `timing_window` must be one of `immediate` or `short_drift`
- `event_type` and `direction` must be non-empty when defining event policies
- unknown top-level structures inside `scoring_policy` are rejected

Failure mode:

- raise a `ValueError` with a concrete config message
- do not silently ignore malformed scoring policy config

## Implementation Plan

### Config Loading

Extend `src/signal_graph/config.py` with a helper that reads and validates the optional `scoring_policy` section from the loaded TOML config.

### Policy Merge

Add merge logic to `src/signal_graph/services/scoring_policy.py` so:

- built-in defaults remain defined in code
- local config is parsed into typed policy models
- the effective merged policy is returned by `get_scoring_policy()`

### Consumers

No new consumer behavior should be introduced beyond reading the merged policy:

- `rank.py` keeps resolving base score and description from policy
- `timing.py` keeps resolving timing from policy
- `explain.py` keeps resolving description and rationale from policy

### Examples And Docs

Add a checked-in example file:

- `docs/examples/scoring-policy.example.toml`

Update documentation:

- `README.md`: add a “Customizing Scoring Policy” section
- `docs/runbooks/operator-guide.md`: add config location, precedence, validation behavior, and concrete examples
- `docs/runbooks/analyst-agent-guide.md`: add a short note that local policy changes can alter ranking order and memo rationale

## Examples To Document

Example 1: make `capex_cut` more punitive for upstream suppliers.

Example 2: define a new event policy such as `export_control` with immediate ETF spillover and slower downstream customer read-through.

Example 3: override only a path description without changing the score.

## Testing

Add tests for:

- parsing a valid local scoring policy config
- rejecting malformed scoring policy config
- merging path overrides correctly
- merging event overrides correctly
- using a new locally defined event policy in ranking
- using the merged rationale in memo output

## Recommended Sequence

1. Add typed config parsing for `scoring_policy`
2. Add merge logic in `scoring_policy.py`
3. Add focused service tests for parse and merge behavior
4. Add rank and explain tests for config-driven behavior
5. Add checked-in example file and documentation

## Acceptance Criteria

The feature is complete when all of the following are true:

- removing local policy config preserves current behavior
- a local TOML override changes ranking/timing/memo behavior without code edits
- malformed policy config fails with a clear message
- the repo contains a copyable example policy file
- README and runbooks document the config shape and precedence accurately
