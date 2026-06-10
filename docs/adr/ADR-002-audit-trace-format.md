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
`prev_hash` and `event_hash`, where
`event_hash = sha256(canonical(event, prev_hash))`. The first event of a trace chains from a single well-known genesis
sentinel (`0` * 64). Verification recomputes the chain end to end.


## Event taxonomy

| Kind | Emitted when |
|---|---|
| `plan_created` | The planner produces a new plan |
| `plan_revised` | The planner revises after critic feedback |
| `tool_call` | The executor invokes a governed tool (pre-policy decision) |
| `tool_result` | A governed tool returns |
| `critique` | The critic scores the current plan/results |
| `synthesis` | The synthesizer emits the final answer |
| `error` | A role or tool raised an unrecoverable error |

| `approval_requested` | A policy-gated tool call pauses for a human |
| `approval_resolved` | The approval queue resolves the request |
| `session_opened` | A new orchestration session registers its trace |


## Canonical form

The canonical form is versioned as `v1`; a future `v2` must keep `v1`
verification working for old traces.


Hashes are computed over `json.dumps(event, sort_keys=True, separators=(",",
":"))` covering exactly: `trace_id`, `kind`, `payload`, `prev_hash`. Anything
else (timestamps, server-assigned ids) stays outside the hash so replays verify
against the original values only.


## Genesis sentinel

The first event of every trace chains from `GENESIS_HASH = "0" * 64`.
There is exactly one sentinel; it is not a secret.

## Replay procedure

1. Fetch the trace's events ordered by `created_at` (`/audit/{trace_id}`,
   cursor-paginated).
2. Recompute each event's hash from its canonical form and the running
   previous hash.
3. Compare against the stored `event_hash` with a constant-time comparison;
   any mismatch flags tampering or a
   dropped or reordered event at exactly that position.
4. With the chain verified, re-run orchestration deterministically from the
   recorded tool results, comparing outputs against the recorded synthesis.
