/**
 * layout.ts --- deterministic topological layout for the run canvas
 *
 * Contains:
 *   PositionedTask: one task placed at canvas coordinates
 *   LayoutSpacing: the column and row gaps a layout pass is laid out on
 *   COLUMN_WIDTH: horizontal gap between two topological columns
 *   ROW_HEIGHT: vertical gap between two tasks sharing a column
 *   levelTasks(): assigns each task its longest path length from a root
 *   layoutTasks(): places tasks in topological columns, cycle-checked
 */

import type { RunViewerTask } from "./graph-model";

export const COLUMN_WIDTH = 260;
export const ROW_HEIGHT = 120;

export interface PositionedTask {
  id: string;
  x: number;
  y: number;
}

export interface LayoutSpacing {
  columnWidth: number;
  rowHeight: number;
}

const DEFAULT_SPACING: LayoutSpacing = {
  columnWidth: COLUMN_WIDTH,
  rowHeight: ROW_HEIGHT,
};

/**
 * Assigns each task the length of its longest dependency path from a root.
 *
 * Runs Kahn's algorithm, so any task still holding unresolved dependencies once
 * the queue drains belongs to a cycle, which is reported as a null result. A
 * dependency on a task the plan has not streamed yet is ignored rather than
 * treated as a cycle, so a half-arrived plan still lays out.
 *
 * @param tasks - Runtime-planned tasks carrying the ids they depend on.
 * @returns levels - Column index per task id, or null when the graph has a cycle.
 */
export function levelTasks(
  tasks: readonly RunViewerTask[],
): ReadonlyMap<string, number> | null {
  if (tasks.length === 0) {
    return new Map();
  }
  const planned = new Set(tasks.map((task) => task.id));
  const remaining = new Map<string, number>();
  const dependents = new Map<string, string[]>();
  const levels = new Map<string, number>();

  for (const task of tasks) {
    const dependencies = task.dependsOn.filter((id) => planned.has(id));
    remaining.set(task.id, dependencies.length);
    for (const dependency of dependencies) {
      dependents.set(dependency, [
        ...(dependents.get(dependency) ?? []),
        task.id,
      ]);
    }
  }

  const queue = tasks
    .filter((task) => remaining.get(task.id) === 0)
    .map((task) => task.id);
  for (const id of queue) {
    levels.set(id, 0);
  }

  while (queue.length > 0) {
    const id = queue.shift();
    if (id === undefined) {
      break;
    }
    for (const dependent of dependents.get(id) ?? []) {
      const promoted = Math.max(
        levels.get(dependent) ?? 0,
        (levels.get(id) ?? 0) + 1,
      );
      levels.set(dependent, promoted);
      const left = (remaining.get(dependent) ?? 0) - 1;
      remaining.set(dependent, left);
      if (left === 0) {
        queue.push(dependent);
      }
    }
  }

  return levels.size === tasks.length ? levels : null;
}

/**
 * Places tasks in topological columns, leaving column zero to the orchestrator.
 *
 * Each column is centred on the orchestrator's row rather than stacked downward,
 * so a plan that fans out reads as a balanced fan instead of drifting off screen.
 *
 * @param tasks - Runtime-planned tasks carrying the ids they depend on.
 * @param spacing - Column and row gaps to lay the graph out on.
 * @returns placements - One canvas position per task, empty when a cycle is found.
 */
export function layoutTasks(tasks: readonly RunViewerTask[], spacing: Readonly<LayoutSpacing> = DEFAULT_SPACING): PositionedTask[] {
  const levels: ReadonlyMap<string, number> | null = levelTasks(tasks);
  if (levels === null) {
    return [];
  }
  const columnHeight = new Map<number, number>();
  for (const task of tasks) {
    const column = levels.get(task.id) ?? 0;
    columnHeight.set(column, (columnHeight.get(column) ?? 0) + 1);
  }

  const rowsPerColumn = new Map<number, number>();
  return tasks.map((task) => {
    const column = levels.get(task.id) ?? 0;
    const row = rowsPerColumn.get(column) ?? 0;
    const height = columnHeight.get(column) ?? 1;
    rowsPerColumn.set(column, row + 1);
    return {
      id: task.id,
      x: (column + 1) * spacing.columnWidth,
      y: (row - (height - 1) / 2) * spacing.rowHeight,
    };
  });
}
