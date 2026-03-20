# Product Overview

## Summary

`Signal Graph` is a local, CLI-first trading research toolkit for event-driven idea generation and memo production.

Its purpose is not to automate trading. Its purpose is to structure the path from a raw event to an explainable, provenance-aware trade hypothesis.

## Problem

Analysts and coding agents can gather headlines quickly, but raw event streams are noisy:

- the same event appears across multiple sources
- evidence quality varies by source type
- entity resolution is often incomplete
- downstream reasoning can get mixed with unsupported storytelling

Most tooling either stops at note-taking or jumps directly to opaque scoring. `Signal Graph` is meant to sit in between, making the decision chain explicit.

## Product Shape

The product is best understood as a workflow:

`raw event -> normalized event candidate -> researched bundle -> graph event -> ranked candidates -> memo`

That workflow is implemented as deterministic CLI commands and local artifacts so it can be operated by humans or coding agents.

## Who It Is For

- A discretionary analyst working from breaking headlines and thematic research
- A research engineer building a reproducible event-to-thesis workflow
- A coding agent that needs explicit commands, provenance boundaries, and local artifacts
- A product stakeholder evaluating whether the workflow is coherent and extensible

## Intended Use Cases

### 1. Manual Event Capture

An analyst pastes an observation such as "supplier disruption" or "capex cut" and wants to formalize it into a structured research flow.

### 2. Connector-Driven Research Intake

A connector returns public-web or premium-feed material that should be normalized into the same canonical pipeline.

### 3. Graph-Based Spillover Reasoning

Once an event is researched, the system can reason about likely beneficiaries, victims, peers, or thematic instruments through explicit graph paths.

### 4. Memo Generation For Decision Support

The final output is a memo artifact that distinguishes:

- confirmed fact
- graph implication
- assistant inference

## What Makes It Different

- CLI-native instead of dashboard-first
- provenance-aware instead of summary-first
- graph-reasoned instead of keyword-related
- designed for agent operation, not just human clicking

## Current Maturity

This repository is an MVP.

It already supports the full local command chain, test coverage for the manual flow, and documentation for operators and agents. Several parts remain intentionally stubbed so the contract can stabilize before deeper market-data or graph logic is added.

## Non-Goals

- execution or brokerage integration
- fully autonomous trading
- production-grade low-latency ingestion in the current cut
- black-box recommendation generation without auditability
