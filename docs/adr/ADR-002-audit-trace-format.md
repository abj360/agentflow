# ADR-002: Audit trace format — hash-chained, replayable event log

- Status: Accepted
- Date: 2026-05-08
- Deciders: Peter, Kenny

## Context

Every orchestration run must be reconstructable after the fact: for incident
review, for cost attribution, for compliance, and for proving to enterprise
system did what it claims.

A plain log table can be edited without detection.

## Decision

Each run emits an ordered chain of `audit_events` rows. Every event carries
`prev_hash` and `event_hash`, where `event_hash = sha256(canonical(event,
prev_hash))`. The first event of a trace chains from a well-known genesis
sentinel (`0` * 64). Verification recomputes the chain end to end.
