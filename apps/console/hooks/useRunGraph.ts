/**
 * useRunGraph.ts --- folds the live trace stream into the graph the canvas draws
 *
 * Contains:
 *   RunGraph: the tasks and edge firings the canvas renders for one run
 *   applyStructuralEvent(): folds one structural frame into a task list
 *   useRunGraph(): keeps a run's task list and edge pulses in step with the socket
 */

"use client";

import { useMemo } from "react";

import { edgeId, type EdgePulse } from "../lib/edge-pulse";
import type { RunViewerTask } from "../lib/graph-model";
import {
  isStructuralEvent,
  useTraceSocket,
  type StructuralEvent,
} from "./useTraceSocket";

export interface RunGraph {
  tasks: RunViewerTask[];
  pulses: EdgePulse[];
}

/**
 * Folds one structural frame into the task list and edge firings built so far.
 *
 * @param graph - The graph assembled from every earlier frame.
 * @param event - The structural frame that just arrived.
 * @returns graph - The graph with this frame applied.
 */
export function applyStructuralEvent(
  graph: RunGraph,
  event: StructuralEvent,
): RunGraph {
  if (event.kind === "node_created") {
    return { ...graph, tasks: [...graph.tasks, event.task] };
  }
  if (event.kind === "edge_created") {
    return {
      ...graph,
      pulses: [
        ...graph.pulses,
        { id: edgeId(event.from, event.to), firedAt: Date.now() },
      ],
    };
  }
  if (event.kind === "node_status_changed") {
    return {
      ...graph,
      tasks: graph.tasks.map((task) =>
        task.id === event.id ? { ...task, status: event.status } : task,
      ),
    };
  }
  return graph;
}

/**
 * Keeps a run's task list and edge firings in step with the live trace socket.
 *
 * @param runId - Identifier of the run to follow.
 * @returns graph - The tasks spawned so far and the edges currently firing.
 */
export function useRunGraph(runId: string): RunGraph {
  const events = useTraceSocket(runId);

  return useMemo(
    () =>
      events
        .filter(isStructuralEvent)
        .reduce(applyStructuralEvent, { tasks: [], pulses: [] }),
    [events],
  );
}
