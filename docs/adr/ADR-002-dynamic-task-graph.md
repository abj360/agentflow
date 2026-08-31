# ADR-002: Dynamic task graph — planner-built topology, rendered live

- Status: Accepted
- Date: 2026-08-10
- Last reviewed: 2026-08-31
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
branch that happened to run last would get none of it. The bound itself stays
at three: raising it was never the problem, sharing it was.

## Validating before rendering

A planner that replans mid-run can emit a `dependsOn` cycle. `graph_validator.py`
runs before any structural event is written to a WebSocket frame, so a cyclic,
duplicated, or dangling dependency raises server-side instead of reaching the
canvas, where a cycle would empty it. Validation runs in three places on
purpose: `planner_node()` on every replan, `build_graph()` before wiring, and
`events_for_plan()` before emitting.

## One frame per plan, not one per node

A twelve-task plan used to mean twelve WebSocket frames, and the console laid
the canvas out again on each one. Structural events are batched into a single
`graph_delta` frame, so a plan costs one layout pass. The console unpacks the
batch before folding it, so nothing downstream knows the difference.

## Reporting status without knowing about WebSockets

`build_graph()` takes an optional status sink and calls it as each task enters
and leaves `running`. The graph stays ignorant of transport; the API layer is
what turns those calls into `node_status_changed` frames.

## Parallel branches, not one long chain

A plan whose objectives do not reference one another is fanned out into
independent roots rather than chained. Chaining is easy to emit and wrong to
look at: the canvas would draw a single line, and the revision budget would be
shared by steps that have nothing to do with each other.

## Alternatives considered

- **Keep the fixed topology and attach node metadata to it.** Rejected: the
  metadata would describe steps the executed graph does not actually have, so
  the console would still be guessing at structure nobody declared.
- **Let the console infer structure from trace event ordering.** Rejected:
  arrival order is not a dependency graph. Two events arriving in sequence say
  nothing about whether one waited on the other.
- **Validate the DAG in the console.** Rejected: fail closed on the server. A
  cycle that reaches the browser is already a frame we should not have sent.
  Validating in one place turned out to be too few places: the first version
  checked only the initial plan, and a mid-run replan emptied the canvas until
  `planner_node()` and `build_graph()` both started validating too. The error
  now says which stage rejected the plan, because the first incident cost an
  hour working out which one had not.

## What the console is allowed to decide

Layout, animation, and node species are the console's business; structure is
not. The species a node draws as is derived from its assignee client-side,
because it is a rendering choice. Its dependencies are not derived anywhere:
they arrive as `dependsOn` and are drawn as given.

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
