/**
 * graph-model.ts --- the task graph the canvas renders, as the API streams it
 *
 * Contains:
 *   TaskStatus: lifecycle states a task node moves through
 *   RunViewerTask: one runtime-planned task as the API streams it
 *   TaskSpecies: the node species the canvas renders a task as
 *   ORCHESTRATOR_ID: id of the fixed central node every run hangs off
 *   speciesFor(): resolves which species the canvas renders a task as
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

export type TaskSpecies = "research" | "tool-call" | "file-op" | "approval";

const SPECIES_BY_ASSIGNEE: Record<string, TaskSpecies> = {
  researcher: "research",
  executor: "tool-call",
  writer: "file-op",
};

/**
 * Resolves which node species the canvas renders a task as.
 *
 * @param task - The runtime-planned task about to be rendered.
 * @returns species - Species name matching a key in the canvas node type map.
 */
export function speciesFor(task: RunViewerTask): TaskSpecies {
  if (task.status === "awaiting-approval") {
    return "approval";
  }
  return SPECIES_BY_ASSIGNEE[task.assignee];
}
