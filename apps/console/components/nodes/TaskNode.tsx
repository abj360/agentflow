/**
 * TaskNode.tsx --- the shared shell every task node species renders inside
 *
 * Contains:
 *   TaskNodeData: what the canvas hands one task node
 *   TaskNode: renders one planned task, spawning in when it first mounts
 */

"use client";

import type { ReactNode } from "react";
import { Handle, Position, type NodeProps } from "reactflow";

import type { TaskSpecies, TaskStatus } from "../../lib/graph-model";
import type { Approval } from "../../lib/api";

export interface TaskNodeData {
  title: string;
  assignee: string;
  status: TaskStatus;
  tokens: number;
  retries: number;
  toolCallCount: number;
  approval?: Approval;
  onResolve?: (approvalId: string) => void;
}

/**
 * Renders one planned task, spawning in when the node first mounts.
 *
 * @param props.data - Title, assignee, status, and cost counters for the task.
 * @param props.species - Species class the node is styled and labelled as.
 * @param props.detail - Extra line the species wants under the assignee.
 * @param props.children - Body a species expands the node into, when it has one.
 * @returns The task node element.
 */
export function TaskNode({
  data,
  species,
  detail,
  children,
}: NodeProps<TaskNodeData> & {
  species: TaskSpecies;
  detail?: string;
  children?: ReactNode;
}) {
  return (
    <div
      className={`canvas-node canvas-node--${species} canvas-node--spawning canvas-node--${data.status}`}
    >
      <Handle type="target" position={Position.Left} />
      <span className={`canvas-node__dot canvas-node__dot--${data.status}`} />
      <strong>{data.title}</strong>
      <span className="canvas-node__meta">{data.assignee}</span>
      {detail === undefined ? null : (
        <span className="canvas-node__meta">{detail}</span>
      )}
      {data.retries === 0 ? null : (
        <span className="canvas-node__retries">{data.retries} retries</span>
      )}
      {children}
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
