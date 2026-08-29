/**
 * relaxation.spec.ts --- tests for the force relaxation layered on the layout
 *
 * Contains:
 *   relaxation specs: column discipline, separation, and the trivial cases
 */

import { expect, test } from "@playwright/test";

import { COLUMN_WIDTH } from "../../lib/layout";
import {
  COLUMN_STRENGTH,
  MIN_RELAXATION_TICKS,
  ROW_STRENGTH,
  RELAXATION_TICKS,
  relaxPositions,
  ticksFor,
} from "../../lib/relaxation";

test("a single node is handed back untouched", () => {
  const placed = [{ id: "a", x: 10, y: 20 }];
  expect(relaxPositions(placed)).toEqual(placed);
});

test("an empty layout relaxes to nothing", () => {
  expect(relaxPositions([])).toEqual([]);
});

test("nodes stay near the column the topology put them in", () => {
  const relaxed = relaxPositions([
    { id: "a", x: COLUMN_WIDTH, y: 0 },
    { id: "b", x: COLUMN_WIDTH, y: 10 },
  ]);
  for (const node of relaxed) {
    expect(Math.abs(node.x - COLUMN_WIDTH)).toBeLessThan(COLUMN_WIDTH / 2);
  }
});

test("overlapping nodes are pushed apart", () => {
  const relaxed = relaxPositions([
    { id: "a", x: COLUMN_WIDTH, y: 0 },
    { id: "b", x: COLUMN_WIDTH, y: 0 },
  ]);
  const [first, second] = relaxed;
  expect(
    Math.hypot(
      (first?.x ?? 0) - (second?.x ?? 0),
      (first?.y ?? 0) - (second?.y ?? 0),
    ),
  ).toBeGreaterThan(0);
});

test("a small plan gets the full tick budget", () => {
  expect(ticksFor(4)).toBe(RELAXATION_TICKS);
});

test("a long run never drops below the tick floor", () => {
  expect(ticksFor(4000)).toBe(MIN_RELAXATION_TICKS);
});

test("a plan past the ceiling keeps the skeleton untouched", () => {
  const wide = Array.from({ length: 200 }, (unused, index) => ({
    id: `task-${index}`,
    x: COLUMN_WIDTH,
    y: index,
  }));
  expect(relaxPositions(wide)).toEqual(wide);
});

test("a settled node does not move when a new one spawns beside it", () => {
  const settled = { id: "a", x: COLUMN_WIDTH, y: 0 };
  const relaxed = relaxPositions(
    [settled, { id: "b", x: COLUMN_WIDTH, y: 0 }],
    new Map([[settled.id, settled]]),
  );
  expect(relaxed.find((node) => node.id === "a")).toEqual(settled);
});

test("the newly spawned node is the one that moves", () => {
  const settled = { id: "a", x: COLUMN_WIDTH, y: 0 };
  const relaxed = relaxPositions(
    [settled, { id: "b", x: COLUMN_WIDTH, y: 0 }],
    new Map([[settled.id, settled]]),
  );
  const spawned = relaxed.find((node) => node.id === "b");
  expect(spawned?.y).not.toBe(0);
});

test("a first pass with nothing pinned still relaxes", () => {
  const relaxed = relaxPositions([
    { id: "a", x: COLUMN_WIDTH, y: 0 },
    { id: "b", x: COLUMN_WIDTH, y: 0 },
  ]);
  expect(relaxed).toHaveLength(2);
});

test("pinning a node the layout no longer has is ignored", () => {
  const gone = { id: "gone", x: 0, y: 0 };
  const relaxed = relaxPositions(
    [
      { id: "a", x: COLUMN_WIDTH, y: 0 },
      { id: "b", x: COLUMN_WIDTH, y: 40 },
    ],
    new Map([[gone.id, gone]]),
  );
  expect(relaxed.map((node) => node.id)).toEqual(["a", "b"]);
});

test("the column force is the stronger of the two", () => {
  expect(COLUMN_STRENGTH).toBeGreaterThan(ROW_STRENGTH);
});
