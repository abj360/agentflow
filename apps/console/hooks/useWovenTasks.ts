/**
 * useWovenTasks.ts --- reveals a plan's nodes one at a time, as it is woven
 *
 * Contains:
 *   WEAVE_STEP_MS: how long the canvas waits between revealing two nodes
 *   prefersReducedMotion(): whether this browser has asked for less movement
 *   useWovenTasks(): reveals newly planned tasks one after another
 */

"use client";

import { useEffect, useMemo, useState } from "react";

import type { RunViewerTask } from "../lib/graph-model";

export const WEAVE_STEP_MS = 260;

/**
 * Reports whether this browser has asked for less movement.
 *
 * @returns reduced - True when the reviewer has reduced motion turned on.
 */
export function prefersReducedMotion(): boolean {
  return (
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

/**
 * Reveals newly planned tasks one after another rather than all at once.
 *
 * A whole plan reaches the console inside a single frame, which is what keeps a
 * twelve-task plan to one layout pass. Revealing it in one paint, though, makes
 * the graph look precomputed: the point of the canvas is that the reviewer sees
 * the coordinator weaving it. So the frame stays batched on the wire and the
 * reveal is staggered here, where it costs nothing but a timer.
 *
 * @param tasks - Every task the run has been told about so far.
 * @param stepMs - How long to wait between revealing two nodes.
 * @returns woven - The tasks revealed so far, in plan order.
 */
export function useWovenTasks(
  tasks: readonly RunViewerTask[],
  stepMs: number = WEAVE_STEP_MS,
): RunViewerTask[] {
  const [shown, setShown] = useState(0);

  useEffect(() => {
    if (shown > tasks.length) {
      setShown(tasks.length); // a new run replaced the plan the canvas had
      return;
    }
    if (shown >= tasks.length) {
      return;
    }
    if (prefersReducedMotion()) {
      setShown(tasks.length);
      return;
    }
    const timer = setTimeout(
      () => setShown((count) => count + 1),
      shown === 0 ? 0 : stepMs,
    );
    return () => clearTimeout(timer);
  }, [shown, tasks.length, stepMs]);

  return useMemo(() => tasks.slice(0, shown), [tasks, shown]);
}
