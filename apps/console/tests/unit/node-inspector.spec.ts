/**
 * node-inspector.spec.ts --- tests for what a node reports when it is opened
 *
 * Contains:
 *   TASK: a settled task the duration is read off
 *   duration specs: unfinished, sub-minute, and long-running tasks
 *   fold specs: the timing and output a status frame carries onto a task
 */

import { expect, test } from "@playwright/test";

import { duration } from "../../components/NodeInspector";
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

test("a task that has not settled reports no duration", () => {
  expect(duration(TASK)).toBe("—");
});

test("a task that started but has not finished reports no duration", () => {
  expect(duration({ ...TASK, startedAt: 10 })).toBe("—");
});

test("a short task is reported in seconds", () => {
  expect(duration({ ...TASK, startedAt: 10, finishedAt: 45.3 })).toBe("35.3 s");
});

test("a long task is reported in minutes", () => {
  expect(duration({ ...TASK, startedAt: 0, finishedAt: 90 })).toBe("1.5 min");
});

test("a running frame starts the task's clock", () => {
  const graph = applyStructuralEvent(
    { tasks: [TASK], pulses: [], feedback: [] },
    { kind: "node_status_changed", id: "task-1", status: "running", at: 12 },
  );
  expect(graph.tasks[0].startedAt).toBe(12);
});

test("a done frame stops the clock and keeps the output", () => {
  const graph = applyStructuralEvent(
    { tasks: [{ ...TASK, startedAt: 12 }], pulses: [], feedback: [] },
    {
      kind: "node_status_changed",
      id: "task-1",
      status: "done",
      at: 20,
      output: "what the agent produced",
    },
  );
  expect(graph.tasks[0].finishedAt).toBe(20);
  expect(graph.tasks[0].output).toBe("what the agent produced");
});

test("a later frame never erases an output already received", () => {
  const withOutput = applyStructuralEvent(
    { tasks: [TASK], pulses: [], feedback: [] },
    {
      kind: "node_status_changed",
      id: "task-1",
      status: "done",
      output: "kept",
    },
  );
  const after = applyStructuralEvent(withOutput, {
    kind: "node_status_changed",
    id: "task-1",
    status: "running",
  });
  expect(after.tasks[0].output).toBe("kept");
});
