/**
 * graph-model.ts --- the task graph the canvas renders, as the API streams it
 *
 * Contains:
 *   TaskStatus: lifecycle states a task node moves through
 *   RunViewerTask: one runtime-planned task as the API streams it
 *   ORCHESTRATOR_ID: id of the fixed central node every run hangs off
 */

export type TaskStatus =
  | "pending"
  | "running"
  | "awaiting-approval"
  | "done"
  | "failed";

export interface RunViewerTask {
  id: string;
  title: string;
  assignee: string;
  status: TaskStatus;
  dependsOn: string[];
  startedAt: number | null;
  finishedAt: number | null;
  tokens: number;
  retries: number;
  toolCallCount: number;
}

export const ORCHESTRATOR_ID = "orchestrator";
