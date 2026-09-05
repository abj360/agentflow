/**
 * edge-pulse.spec.ts --- golden-output tests for edge animation timing
 *
 * Contains:
 *   pulse specs: how long an edge stays lit, when it goes dark, and refiring
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
  // Everything here is expressed relative to PULSE_DURATION_MS, so retuning
  // the animation never turns into a golden-output failure.
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

test("recording one edge drops the edges that already expired", () => {
  const expiring = recordPulse([], "old", START);
  const fresh = recordPulse(expiring, "new", START + PULSE_DURATION_MS);
  expect(fresh.map((pulse) => pulse.id)).toEqual(["new"]);
});

test("edges fired in the same frame are all lit together", () => {
  const both = recordPulse(recordPulse([], "a", START), "b", START);
  expect(activeEdges(both, START).size).toBe(2);
});

test("pulses from separate frames stay lit on their own clocks", () => {
  const first = recordPulse([], "a", START);
  const both = recordPulse(first, "b", START + PULSE_DURATION_MS - 1);
  expect(activeEdges(both, START + PULSE_DURATION_MS - 1).size).toBe(2);
  expect(activeEdges(both, START + PULSE_DURATION_MS).size).toBe(1);
});

test("the newest firing is recorded last", () => {
  const pulses = recordPulse(recordPulse([], "a", START), "b", START + 10);
  expect(pulses.at(-1)?.id).toBe("b");
});

test("nothing is lit before anything has fired", () => {
  expect(activeEdges([], START).size).toBe(0);
});

test("an edge fired in the past is not resurrected", () => {
  const pulses = recordPulse([], "a", START);
  expect(activeEdges(pulses, START + PULSE_DURATION_MS * 3).size).toBe(0);
});

test("a burst of firings on one edge collapses to one pulse", () => {
  const pulses = [0, 100, 200, 300].reduce(
    (carried, offset) => recordPulse(carried, "e", START + offset),
    [] as ReturnType<typeof recordPulse>,
  );
  expect(pulses).toHaveLength(1);
});

test("the pulse window is the same for every edge", () => {
  const pulses = recordPulse(recordPulse([], "a", START), "b", START);
  expect(activeEdges(pulses, START + PULSE_DURATION_MS - 1).size).toBe(2);
  expect(activeEdges(pulses, START + PULSE_DURATION_MS).size).toBe(0);
});

test("an edge id round-trips through the pulse list", () => {
  const id = edgeId("orchestrator", "task-1");
  expect([...activeEdges(recordPulse([], id, START), START)]).toEqual([id]);
});
