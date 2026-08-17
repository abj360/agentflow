/**
 * edge-pulse.spec.ts --- golden-output tests for edge animation timing
 *
 * Contains:
 *   edge pulse specs: how long an edge stays lit, and when it goes dark again
 */

import { expect, test } from "@playwright/test";

import {
  PULSE_DURATION_MS,
  activeEdges,
  edgeId,
  recordPulse,
} from "../../lib/edge-pulse";

const START = 1_000_000;

test("an edge id names both of its ends", () => {
  expect(edgeId("task-1", "task-2")).toBe("task-1->task-2");
});

test("a freshly fired edge is lit", () => {
  const pulses = recordPulse([], edgeId("task-1", "task-2"), START);
  expect([...activeEdges(pulses, START)]).toEqual(["task-1->task-2"]);
});

test("an edge is still lit one tick before the window closes", () => {
  const pulses = recordPulse([], "e", START);
  expect(activeEdges(pulses, START + PULSE_DURATION_MS - 1).size).toBe(1);
});

test("an edge goes dark exactly when the window closes", () => {
  const pulses = recordPulse([], "e", START);
  expect(activeEdges(pulses, START + PULSE_DURATION_MS).size).toBe(0);
});

test("refiring an edge restarts its window instead of stacking", () => {
  const first = recordPulse([], "e", START);
  const second = recordPulse(first, "e", START + 400);
  expect(second).toHaveLength(1);
  expect(activeEdges(second, START + PULSE_DURATION_MS).size).toBe(1);
});
