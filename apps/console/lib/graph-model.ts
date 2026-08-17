/**
 * graph-model.ts --- the task graph the canvas renders, as the API streams it
 *
 * Contains:
 *   TaskStatus: lifecycle states a task node moves through
 *   RunViewerTask: one runtime-planned task as the API streams it
 *   TaskSpecies: the node species the canvas renders a task as
 *   ORCHESTRATOR_ID: id of the fixed central node every run hangs off
 *   speciesFor(): resolves which species the canvas renders a task as
 *   pairApprovals(): pairs each waiting task with a pending approval request
 */

import type { Approval } from "./api";

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

export type TaskSpecies = "research" | "tool-call" | "file-op" | "approval";

const SPECIES_BY_ASSIGNEE: Readonly<Record<string, TaskSpecies>> = {
  researcher: "research",
  executor: "tool-call",
  writer: "file-op",
};

/**
 * Resolves which node species the canvas renders a task as.
 *
 * @param task - The runtime-planned task about to be rendered.
 * @returns species - Species name matching a key in the canvas node type map,
 *   falling back to research for an assignee the console does not know yet.
 */
export function speciesFor(task: Readonly<RunViewerTask>): TaskSpecies {
  if (task.status === "awaiting-approval") {
    return "approval";
  }
  return SPECIES_BY_ASSIGNEE[task.assignee] ?? "research";
}

/**
 * Pairs every task waiting on a reviewer with one pending approval request.
 *
 * The approvals API keys requests by trace rather than by task, so the pairing
 * is positional: waiting tasks and pending approvals both arrive in plan order.
 *
 * @param tasks - Runtime-planned tasks streamed in for this run.
 * @param approvals - Approval requests currently waiting on a reviewer.
 * @returns paired - The approval each waiting task should expand into.
 */
export function pairApprovals(
  tasks: readonly RunViewerTask[],
  approvals: readonly Approval[],
): Map<string, Approval> {
  const paired = new Map<string, Approval>();
  tasks
    .filter((task) => task.status === "awaiting-approval")
    .forEach((task, index) => {
      const approval = approvals[index];
      if (approval !== undefined) {
        paired.set(task.id, approval);
      }
    });
  return paired;
}
