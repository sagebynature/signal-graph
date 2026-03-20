# Product Overview

## Summary

`Signal Graph` is a local, CLI-first trading research toolkit for event-driven idea generation.

Its job is to make the path from a raw event to an explainable hypothesis explicit. It does not try to automate execution or hide reasoning behind a black box.

## The Problem It Solves

Analysts and coding agents can collect headlines quickly, but fast collection does not produce a trustworthy thesis on its own.

Common failure modes:

- The same event appears in several noisy forms
- Evidence quality varies across sources
- Entity resolution is incomplete or wrong
- Downstream narratives outrun the stored evidence
- Ranking logic becomes opaque once it leaves the note-taking stage

Signal Graph is designed to sit between raw intake and final memo output. It forces the research chain into visible stages.

## Product Shape

Signal Graph is best understood as a workflow:

`raw source item -> event candidate -> research bundle -> graph event -> ranked candidates -> memo`

That workflow is implemented as explicit CLI commands, local state, and inspectable artifacts so humans and coding agents can operate it the same way.

## Who It Is For

- A discretionary analyst working from breaking news or thematic research
- A research engineer building a reproducible event-to-thesis workflow
- A coding agent that needs a strict command contract and clear provenance boundaries
- A stakeholder evaluating whether the product shape is coherent and extensible

## Primary Use Cases

### Manual Event Capture

An analyst starts with a note such as "TSMC cuts capex" and wants to formalize it into a repeatable research flow.

### Connector-Driven Intake

A connector returns public or premium-source items that should enter the same normalized pipeline as manual input.

### Graph-Based Spillover Reasoning

Once the event has research attached, the system can reason through explicit relationship paths to likely beneficiaries, victims, peers, customers, suppliers, or ETFs.

### Memo Production For Decision Support

The final output is a memo that distinguishes:

- Confirmed fact
- Graph implication
- Analyst or assistant inference

## What Makes It Different

- CLI-native instead of dashboard-first
- Provenance-aware instead of summary-first
- Graph-reasoned instead of keyword-related
- Designed for coding agents and local operation, not only for human clicking

## Current Maturity

This repository is an MVP. The local operating contract is in place and documented, but some subsystems are intentionally lightweight so the workflow can stabilize first.

The current cut already supports:

- The full local command chain
- A deterministic manual event flow
- SQLite-backed pipeline state
- Neo4j-backed graph ingest and ranking
- Markdown memo output

## What This Cut Does Not Try To Do

- Trade execution or brokerage integration
- Fully autonomous trading
- Production-grade low-latency ingestion
- Opaque recommendation generation without auditability

## Read Next

- Landing page: [`../../README.md`](../../README.md)
- Architecture: [`../architecture/system-overview.md`](../architecture/system-overview.md)
- Local operation: [`../runbooks/operator-guide.md`](../runbooks/operator-guide.md)
- Analyst workflow: [`../runbooks/analyst-agent-guide.md`](../runbooks/analyst-agent-guide.md)
