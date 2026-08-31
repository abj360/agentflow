/**
 * layout.spec.ts --- snapshot tests for the ported topological layout
 *
 * Contains:
 *   task(): builds one runtime-planned task for a layout fixture
 *   layout specs: column assignment, row packing, and cycle rejection
 */

import { expect, test } from "@playwright/test";

import type { RunViewerTask } from "../../lib/graph-model";
import {
  COLUMN_WIDTH,
  ROW_HEIGHT,
  layoutTasks,
  levelTasks,
} from "../../lib/layout";

/**
 * Builds one runtime-planned task for a layout fixture.
 *
 * @param id - Identifier the layout keys the task on.
 * @param dependsOn - Ids the task waits on.
 * @returns task - A pending task carrying no cost counters.
 */
function task(id: string, dependsOn: string[] = []): RunViewerTask {
  return {
    id,
    title: id,
    assignee: "executor",
    status: "pending",
    dependsOn,
    startedAt: null,
    finishedAt: null,
    tokens: 0,
    retries: 0,
    toolCallCount: 0,
  };
}

test("a straight chain lands one task per column", () => {
  const levels = levelTasks([task("a"), task("b", ["a"]), task("c", ["b"])]);
  expect(levels).not.toBeNull();
  expect([...(levels ?? [])]).toEqual([
    ["a", 0],
    ["b", 1],
    ["c", 2],
  ]);
});

test("a task sits in the column after its longest path, not its shortest", () => {
  const levels = levelTasks([
    task("a"),
    task("b", ["a"]),
    task("c", ["a", "b"]),
  ]);
  expect(levels?.get("c")).toBe(2);
});

test("independent roots share a column, centred on the orchestrator row", () => {
  const placed = layoutTasks([task("a"), task("b")]);
  expect(placed).toEqual([
    { id: "a", x: COLUMN_WIDTH, y: -ROW_HEIGHT / 2 },
    { id: "b", x: COLUMN_WIDTH, y: ROW_HEIGHT / 2 },
  ]);
});

test("a single task in a column sits on the orchestrator row", () => {
  expect(layoutTasks([task("a")])).toEqual([
    { id: "a", x: COLUMN_WIDTH, y: 0 },
  ]);
});

test("a cycle lays out nothing rather than hanging", () => {
  const placed = layoutTasks([task("a", ["b"]), task("b", ["a"])]);
  expect(placed).toEqual([]);
});

test("an empty plan lays out nothing", () => {
  expect(layoutTasks([])).toEqual([]);
});

test("a dependency the plan has not streamed yet is ignored", () => {
  const levels = levelTasks([task("b", ["a"])]);
  expect(levels?.get("b")).toBe(0);
});

test("a diamond keeps its join in the last column", () => {
  const levels = levelTasks([
    task("root"),
    task("left", ["root"]),
    task("right", ["root"]),
    task("join", ["left", "right"]),
  ]);
  expect(levels?.get("join")).toBe(2);
  expect(levels?.get("left")).toBe(levels?.get("right"));
});

test("a wide fan spreads evenly around the orchestrator row", () => {
  const placed = layoutTasks([task("a"), task("b"), task("c")]);
  expect(placed.map((node) => node.y)).toEqual([-ROW_HEIGHT, 0, ROW_HEIGHT]);
});

test("a task that joins two columns lands after the deeper one", () => {
  const levels = levelTasks([
    task("a"),
    task("b", ["a"]),
    task("c", ["b"]),
    task("d", ["a", "c"]),
  ]);
  expect(levels?.get("d")).toBe(3);
});

test("a caller can widen the spacing without touching the topology", () => {
  const placed = layoutTasks([task("a"), task("b", ["a"])], {
    columnWidth: 100,
    rowHeight: 40,
  });
  expect(placed.map((node) => node.x)).toEqual([100, 200]);
});

test("levels are stable no matter what order tasks arrive in", () => {
  const forwards = levelTasks([task("a"), task("b", ["a"]), task("c", ["b"])]);
  const backwards = levelTasks([task("c", ["b"]), task("b", ["a"]), task("a")]);
  expect(forwards?.get("c")).toBe(backwards?.get("c"));
});

test("a task depending on itself lays out nothing", () => {
  expect(layoutTasks([task("a", ["a"])])).toEqual([]);
});

test("a duplicate dependency does not shift the column", () => {
  const levels = levelTasks([task("a"), task("b", ["a", "a"])]);
  expect(levels?.get("b")).toBe(1);
});
