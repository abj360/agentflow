# ADR-001: Orchestration pattern — planner/executor/synthesizer/critic loop

- Status: Accepted
- Date: 2026-04-28
- Deciders: Peter

## Context

agentflow runs multi-step agent work that must stay auditable, budgeted, and
interruptible, and replayable. A single monolithic agent call gives us none
of those levers:
no per-step audit events, no per-tool policy checks, no budget hooks, and no
place for a human to intervene mid-run.

## Decision

Orchestration runs as an explicit state machine with four roles:

1. **Planner** turns the task into an ordered plan (no execution here).
2. **Executor** runs each plan step through the governed MCP tool layer.
3. **Synthesizer** merges step outputs into the final answer.
4. **Critic** reviews plans and outputs, accepting or requesting revision.

The loop is implemented as a LangGraph `StateGraph` so transitions are
explicit, testable, and replayable end to end from the audit log.


## Alternatives considered

- **Single monolithic agent call.** Rejected: no per-step audit trail, no place
  for policy checks between steps, and no way to bound cost mid-run.
- **Hard-coded if/else orchestration.** Rejected: transitions must stay explicit
  and testable; a state graph gives us that plus replay from the audit log.
- **Autonomous unbounded loop.** Firmly rejected: an unbounded planner/critic loop is
  a cost incident waiting to happen — see the bound in `loop.py`.


## Bounding the loop

The planner/critic cycle is capped at `MAX_REVISIONS = 3` per session. Past
the cap the run ends with a `revision-bounded` status and the full trace is
preserved for review.

Unbounded agent loops are a cost incident, not a feature.
