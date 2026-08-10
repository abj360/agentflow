# ADR-002: Dynamic task graph — planner-built topology, rendered live

- Status: Accepted
- Date: 2026-08-10
- Deciders: Peter
- Reviewers: David, Yannick
- Supersedes: the fixed-topology assumption in ADR-001

## Context

ADR-001 wired orchestration as a fixed `planner → executor → critic` LangGraph.
That shape is honest about the *roles* in a run but silent about the *work*:
every run, whatever the task, is the same three boxes, so the console can only
render a flat trace log. There is no node identity to hang a status, a token
count, or an approval off.

## Decision

The planner emits its task list at run time. Each task carries an `id`, a
`title`, an `assignee`, a `status`, and a `dependsOn` array, and `build_graph()`
wires the LangGraph from those dependencies instead of from a hard-coded
topology. The console derives its picture from the same `dependsOn` edges, so
what is on screen and what is executing are the same graph, not two
representations that can drift.

## What ADR-001 still holds

The four roles stay. The `MAX_REVISIONS = 3` bound stays, but it now applies per
branch of the plan rather than once per session: a plan with three independent
branches would otherwise make them share a single revision budget, and the
branch that happened to run last would get none of it.

## Validating before rendering

A planner that replans mid-run can emit a `dependsOn` cycle. `graph_validator.py`
runs before any structural event is written to a WebSocket frame, so a cyclic,
duplicated, or dangling dependency raises server-side instead of reaching the
canvas, where a cycle would hang the topological layout.

## Alternatives considered

- **Keep the fixed topology and attach node metadata to it.** Rejected: the
  metadata would describe steps the executed graph does not actually have, so
  the console would still be guessing at structure nobody declared.
- **Let the console infer structure from trace event ordering.** Rejected:
  arrival order is not a dependency graph. Two events arriving in sequence say
  nothing about whether one waited on the other.
- **Validate the DAG in the console.** Rejected: fail closed on the server. A
  cycle that reaches the browser is already a frame we should not have sent.

## Consequences

- `build_graph()` takes the planned task list as an argument, so every caller
  plans before it builds.
- The trace event schema gains `node_created`, `edge_created`, and
  `node_status_changed`, and every consumer of the old flat shape changes with
  it.
- The console's `/traces` and `/approvals` routes fold into a single
  `/run/[id]` screen, because an approval is now a state a node is in rather
  than a queue somewhere else.

## References

- ADR-001: orchestration pattern — the roles, and the revision bound this keeps.
- `apps/api/orchestration/task_planner.py`, `apps/api/orchestration/graph_validator.py`.
