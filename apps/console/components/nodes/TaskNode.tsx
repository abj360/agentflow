/**
 * TaskNode.tsx --- the shared shell every task node species renders inside
 *
 * Contains:
 *   TaskNodeData: what the canvas hands one task node
 *   TaskNode: renders one planned task, spawning in when it first mounts
 */

"use client";

import { Handle, Position, type NodeProps } from "reactflow";

import type { TaskSpecies, TaskStatus } from "../../lib/graph-model";

export interface TaskNodeData {
  title: string;
  assignee: string;
  status: TaskStatus;
  tokens: number;
  toolCallCount: number;
}

/**
 * Renders one planned task, spawning in when the node first mounts.
 *
 * @param props.data - Title, assignee, status, and cost counters for the task.
 * @param props.species - Species class the node is styled and labelled as.
 * @param props.detail - Extra line the species wants under the assignee.
 * @returns The task node element.
 */
export function TaskNode({
  data,
  species,
  detail,
}: NodeProps<TaskNodeData> & {
  species: TaskSpecies;
  detail?: string;
}) {
  return (
    <div
      className={`canvas-node canvas-node--${species} canvas-node--spawning canvas-node--${data.status}`}
    >
      <Handle type="target" position={Position.Left} />
      <strong>{data.title}</strong>
      <span className="canvas-node__meta">{data.assignee}</span>
      {detail === undefined ? null : (
        <span className="canvas-node__meta">{detail}</span>
      )}
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
