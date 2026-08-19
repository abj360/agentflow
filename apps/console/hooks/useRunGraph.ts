/**
 * useRunGraph.ts --- folds the live trace stream into the graph the canvas draws
 *
 * Contains:
 *   TaskGraph: the tasks and edge firings folded out of the structural frames
 *   RunGraph: everything one run screen reads off a single trace connection
 *   applyStructuralEvent(): folds one structural frame into a task list
 *   useRunGraph(): keeps a run's task list and edge pulses in step with the socket
 */

"use client";

import { useMemo } from "react";

import { edgeId, type EdgePulse } from "../lib/edge-pulse";
import type { RunViewerTask } from "../lib/graph-model";
import {
  isLogEvent,
  isStructuralEvent,
  useTraceSocket,
  type StructuralEvent,
  type TraceLogEvent,
} from "./useTraceSocket";

export interface TaskGraph {
  readonly tasks: RunViewerTask[];
  readonly pulses: EdgePulse[];
}

export interface RunGraph extends TaskGraph {
  logs: TraceLogEvent[];
}

/**
 * Folds one structural frame into the task list and edge firings built so far.
 *
 * @param graph - The graph assembled from every earlier frame.
 * @param event - The structural frame that just arrived.
 * @returns graph - The graph with this frame applied.
 */
export function applyStructuralEvent(
  graph: TaskGraph,
  event: StructuralEvent,
): TaskGraph {
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
 * One connection feeds the whole screen: the canvas reads the folded graph and
 * the raw-log panel reads the log lines, so no surface opens a second socket.
 *
 * @returns graph - The tasks, the edges currently firing, and the raw log lines.
 */
export function useRunGraph(runId: string): RunGraph {
  const events = useTraceSocket(runId);

  return useMemo(() => {
    const folded = events
      .filter(isStructuralEvent)
      .reduce(applyStructuralEvent, { tasks: [], pulses: [] });
    return { ...folded, logs: events.filter(isLogEvent) };
  }, [events]);
}
