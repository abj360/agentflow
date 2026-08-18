/**
 * trace-socket.spec.ts --- tests for how the trace stream unpacks batched frames
 *
 * Contains:
 *   frame specs: batched graph deltas, single events, and unreadable frames
 */

import { expect, test } from "@playwright/test";

import { flattenFrame } from "../../hooks/useTraceSocket";

test("a graph delta unpacks into the events it carries", () => {
  const events = flattenFrame({
    kind: "graph_delta",
    runId: "run-1",
    events: [
      { kind: "edge_created", from: "task-1", to: "task-2" },
      { kind: "node_status_changed", id: "task-2", status: "running" },
    ],
  });
  expect(events.map((event) => event.kind)).toEqual([
    "edge_created",
    "node_status_changed",
  ]);
});

test("a single event stays a single event", () => {
  const events = flattenFrame({
    kind: "node_status_changed",
    id: "a",
    status: "done",
  });
  expect(events).toHaveLength(1);
});

test("an empty graph delta yields nothing", () => {
  expect(
    flattenFrame({ kind: "graph_delta", runId: "run-1", events: [] }),
  ).toEqual([]);
});
