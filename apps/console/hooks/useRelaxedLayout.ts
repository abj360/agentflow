/**
 * useRelaxedLayout.ts --- keeps the relaxed canvas layout off the render path
 *
 * Contains:
 *   layoutSignature(): the plan shape a relaxed layout is valid for
 *   useRelaxedLayout(): recomputes the relaxed layout only when the plan changes
 */

"use client";

import { useMemo, useRef } from "react";

import type { RunViewerTask } from "../lib/graph-model";
import { layoutTasks, type PositionedTask } from "../lib/layout";
import { relaxPositions } from "../lib/relaxation";

/**
 * Builds the plan shape a relaxed layout stays valid for.
 *
 * Only structure moves nodes, so status and cost updates -- which arrive far
 * more often than new tasks -- must not re-run the simulation.
 *
 * @param tasks - Runtime-planned tasks streamed in for this run.
 * @returns signature - A string that changes only when the graph shape changes.
 */
export function layoutSignature(
  tasks: readonly Readonly<RunViewerTask>[],
): string {
  return tasks
    .map((task) => `${task.id}:${task.dependsOn.join(",")}`)
    .join("|");
}

/**
 * Recomputes the relaxed layout only when the planned graph shape changes.
 *
 * @param tasks - Runtime-planned tasks streamed in for this run.
 * @returns placements - Relaxed canvas positions, one per task.
 */
export function useRelaxedLayout(
  tasks: readonly RunViewerTask[],
): readonly PositionedTask[] {
  const signature = layoutSignature(tasks);
  const settled = useRef<ReadonlyMap<string, PositionedTask>>(new Map());

  // eslint-disable-next-line react-hooks/exhaustive-deps -- signature stands in
  // for tasks on purpose: that is what makes the throttle a throttle.
  return useMemo(() => {
    const relaxed = relaxPositions(layoutTasks(tasks), settled.current);
    settled.current = new Map(relaxed.map((node) => [node.id, node]));
    return relaxed;
  }, [signature]);
}
