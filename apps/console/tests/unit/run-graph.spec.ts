/**
 * run-graph.spec.ts --- tests for folding structural frames into the canvas graph
 *
 * Contains:
 *   fold specs: spawning, replanning, and status transitions
 */

import { expect, test } from "@playwright/test";

import { applyStructuralEvent } from "../../hooks/useRunGraph";
import type { RunViewerTask } from "../../lib/graph-model";

const TASK: RunViewerTask = {
  id: "task-1",
  title: "gather",
  assignee: "researcher",
  status: "pending",
  dependsOn: [],
  startedAt: null,
  finishedAt: null,
  tokens: 0,
  retries: 0,
  toolCallCount: 0,
};

test("a node frame spawns a task", () => {
  const graph = applyStructuralEvent(
    { tasks: [], pulses: [], feedback: [] },
    { kind: "node_created", task: TASK },
  );
  expect(graph.tasks).toHaveLength(1);
});

test("a replan replaces a task instead of duplicating it", () => {
  const first = applyStructuralEvent(
    { tasks: [], pulses: [], feedback: [] },
    { kind: "node_created", task: TASK },
  );
  const second = applyStructuralEvent(first, {
    kind: "node_created",
    task: { ...TASK, title: "gather again" },
  });
  expect(second.tasks).toHaveLength(1);
  expect(second.tasks[0]?.title).toBe("gather again");
});

test("a status frame moves an existing task", () => {
  const first = applyStructuralEvent(
    { tasks: [], pulses: [], feedback: [] },
    { kind: "node_created", task: TASK },
  );
  const moved = applyStructuralEvent(first, {
    kind: "node_status_changed",
    id: "task-1",
    status: "running",
  });
  expect(moved.tasks[0]?.status).toBe("running");
});

test("a status frame for an unknown task changes nothing", () => {
  const graph = applyStructuralEvent(
    { tasks: [TASK], pulses: [], feedback: [] },
    { kind: "node_status_changed", id: "task-9", status: "done" },
  );
  expect(graph.tasks[0]?.status).toBe("pending");
});

test("an edge frame lights the edge it names", () => {
  const graph = applyStructuralEvent(
    { tasks: [], pulses: [], feedback: [] },
    { kind: "edge_created", from: "orchestrator", to: "task-1" },
  );
  expect(graph.pulses[0]?.id).toBe("orchestrator->task-1");
});

test("a rejection is folded into the return paths", () => {
  const graph = applyStructuralEvent(
    { tasks: [], pulses: [], feedback: [] },
    {
      kind: "edge_feedback",
      from: "task-2",
      to: "task-1",
      note: "add the numbers",
    },
  );
  expect(graph.feedback).toEqual([
    { from: "task-2", to: "task-1", note: "add the numbers" },
  ]);
});

test("a second rejection of the same task replaces the first note", () => {
  const first = applyStructuralEvent(
    { tasks: [], pulses: [], feedback: [] },
    { kind: "edge_feedback", from: "task-2", to: "task-1", note: "first" },
  );
  const second = applyStructuralEvent(first, {
    kind: "edge_feedback",
    from: "task-2",
    to: "task-1",
    note: "second",
  });
  expect(second.feedback).toEqual([
    { from: "task-2", to: "task-1", note: "second" },
  ]);
});
