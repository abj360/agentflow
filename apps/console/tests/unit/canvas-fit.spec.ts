/**
 * canvas-fit.spec.ts --- tests for what re-frames the canvas viewport
 *
 * Contains:
 *   store(): builds the slice of React Flow's store the selector reads
 *   measuredGraph specs: when a spawned node counts as ready to be framed
 */

import { expect, test } from "@playwright/test";
import type { ReactFlowState } from "reactflow";

import { measuredGraph } from "../../components/Canvas";

/**
 * Builds the slice of React Flow's store the selector reads.
 *
 * @param nodes - Node ids with the dimensions React Flow has measured so far.
 * @returns state - A store stand-in carrying just those node internals.
 */
function store(
  nodes: readonly { id: string; width?: number; height?: number }[],
): ReactFlowState {
  return {
    nodeInternals: new Map(nodes.map((node) => [node.id, node])),
  } as unknown as ReactFlowState;
}

test("an unmeasured node reports no size", () => {
  expect(measuredGraph(store([{ id: "orchestrator" }]))).toBe(
    "orchestrator:0x0",
  );
});

test("measuring a node changes the signature", () => {
  const before = measuredGraph(store([{ id: "orchestrator" }]));
  const after = measuredGraph(
    store([{ id: "orchestrator", width: 192, height: 80 }]),
  );
  expect(after).not.toBe(before);
});

test("a spawned node changes the signature even before it is measured", () => {
  const before = measuredGraph(
    store([{ id: "orchestrator", width: 192, height: 80 }]),
  );
  const after = measuredGraph(
    store([{ id: "orchestrator", width: 192, height: 80 }, { id: "task-1" }]),
  );
  expect(after).not.toBe(before);
});

test("a settled graph keeps one stable signature", () => {
  const settled = [
    { id: "orchestrator", width: 192, height: 80 },
    { id: "task-1", width: 144, height: 49 },
  ];
  expect(measuredGraph(store(settled))).toBe(measuredGraph(store(settled)));
});
