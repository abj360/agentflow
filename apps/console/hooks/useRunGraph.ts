/**
 * useRunGraph.ts --- folds the live trace stream into what the canvas draws
 *
 * Contains:
 *   TaskGraph: the tasks and edge firings folded out of the structural frames
 *   RunGraph: everything one run screen reads off a single trace connection
 *   SETTLED: the statuses that stop a task's clock
 *   applyStatus(): applies one status transition to the task it names
 *   applyStructuralEvent(): folds one structural frame into a task list
 *   useRunGraph(): keeps a run's task list and edge pulses in step with the socket
 */

"use client";

import { useMemo } from "react";

import { edgeId, type EdgePulse } from "../lib/edge-pulse";
import type { RunViewerTask, TaskStatus } from "../lib/graph-model";
import {
  isLogEvent,
  isStructuralEvent,
  useTraceSocket,
  type NodeStatusChangedEvent,
  type StructuralEvent,
  type TraceLogEvent,
} from "./useTraceSocket";

export interface TaskGraph {
  readonly tasks: RunViewerTask[];
  readonly pulses: EdgePulse[];
}

export interface RunGraph extends TaskGraph {
  readonly logs: TraceLogEvent[];
  readonly isLive: boolean;
}

const SETTLED = new Set<TaskStatus>(["done", "failed"]);

/**
 * Applies one status transition to the task it names.
 *
 * The transition carries the moment it happened, which is what lets a node
 * report how long it took: the console records the timestamps rather than
 * timing the arrival of frames, so a slow socket cannot inflate a duration.
 *
 * @param task - The task as the canvas has it now.
 * @param event - The transition that just arrived for it.
 * @returns task - The task with the transition applied.
 */
function applyStatus(
  task: RunViewerTask,
  event: NodeStatusChangedEvent,
): RunViewerTask {
  const at = event.at === undefined ? null : event.at;
  return {
    ...task,
    status: event.status,
    output: event.output ?? task.output,
    startedAt: event.status === "running" ? at : task.startedAt,
    finishedAt: SETTLED.has(event.status) ? at : task.finishedAt,
  };
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
    // A replan re-announces tasks the canvas already has; replacing rather than
    // appending keeps one node per task id instead of a duplicate per revision.
    const known = graph.tasks.findIndex((task) => task.id === event.task.id);
    if (known >= 0) {
      return {
        ...graph,
        tasks: graph.tasks.map((task) =>
          task.id === event.task.id ? event.task : task,
        ),
      };
    }
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
        task.id === event.id ? applyStatus(task, event) : task,
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
  const { events, isLive } = useTraceSocket(runId);

  return useMemo(() => {
    const folded = events
      .filter(isStructuralEvent)
      .reduce(applyStructuralEvent, { tasks: [], pulses: [] });
    return { ...folded, logs: events.filter(isLogEvent), isLive };
  }, [events, isLive]);
}
