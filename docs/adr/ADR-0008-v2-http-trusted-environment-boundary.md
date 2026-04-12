# ADR-0008: Keep The HTTP MCP Transport Inside Trusted Environments For The MVP

## Status

Accepted

## Context

V2 needs HTTP transport support for local-network or controlled-host scenarios, but the rewrite is not trying to ship a hardened public multi-tenant service in the MVP. Overreaching on auth and exposure would slow core memory-system work and blur the product boundary.

## Decision Drivers

- maintain a realistic MVP scope
- avoid under-designed public exposure
- support trusted remote hosts and cross-device evaluation
- keep stdio as the default local integration path

## Considered Options

### Option 1: Public HTTP Service From Day One

- Pros: broadest reach
- Cons: high authn/authz, abuse, and hardening burden too early

### Option 2: No HTTP Support In The MVP

- Pros: smallest security surface
- Cons: blocks trusted-network host integrations and parity testing

### Option 3: Trusted-Environment HTTP Boundary

- Pros: enables remote/local-network use without pretending to be a public SaaS
- Cons: docs and tests must be explicit about the boundary

## Decision

Support HTTP MCP transport in the MVP only for trusted environments such as localhost, VPN-connected hosts, or controlled LAN setups. Treat stdio as the default local integration mode and document HTTP as non-public, non-multi-tenant MVP behavior.

## Consequences

### Positive

- transport parity can still be exercised in realistic evals
- scope stays focused on memory-system correctness rather than premature perimeter hardening
- documentation can be honest about what is and is not supported

### Negative

- public deployment stories remain out of scope for now
- operators must understand the trusted-environment assumption before enabling HTTP

## Related Documents

- `docs/integrations/README.md`
- `.omx/plans/test-spec-signal-graph-v2-memory-rewrite.md`
