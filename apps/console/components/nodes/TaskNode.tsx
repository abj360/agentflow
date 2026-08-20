/**
 * TaskNode.tsx --- the shared shell every task node species renders inside
 *
 * Contains:
 *   TaskNodeData: what the canvas hands one task node
 *   spawnStyle(): the inline style that staggers one node's mount animation
 *   NodeCost: renders a task's token and tool-call counters
 *   TaskNode: renders one planned task, spawning in when it first mounts
 */

"use client";

import type { CSSProperties, ReactNode } from "react";
import { Handle, Position, type NodeProps } from "reactflow";

import type { TaskSpecies, TaskStatus } from "../../lib/graph-model";
import type { Approval } from "../../lib/api";

export interface TaskNodeData {
  title: string;
  assignee: string;
  status: TaskStatus;
  tokens: number;
  retries: number;
  spawnDelay: number;
  toolCallCount: number;
  approval?: Readonly<Approval>;
  onResolve?: (approvalId: string) => void;
}

/**
 * Builds the inline style that staggers one node's mount animation.
 *
 * @param spawnDelay - Milliseconds this node waits before it animates in.
 * @returns style - The animation delay React Flow applies to the node shell.
 */
function spawnStyle(spawnDelay: number): CSSProperties {
  return { animationDelay: `${spawnDelay}ms` };
}

/**
 * Renders a task's token and tool-call counters, once it has spent either.
 *
 * @param props.tokens - Model tokens the task has consumed.
 * @param props.toolCallCount - Governed tool calls the task has made.
 * @returns The cost line element, or nothing while the task is free.
 */
function NodeCost({
  tokens,
  toolCallCount,
}: Readonly<{ tokens: number; toolCallCount: number }>) {
  if (tokens === 0 && toolCallCount === 0) {
    return null;
  }
  return (
    <span className="canvas-node__meta">
      {tokens} tok · {toolCallCount} calls
    </span>
  );
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
      style={spawnStyle(data.spawnDelay)}
    >
      <Handle type="target" position={Position.Left} />
      <span
        className={`canvas-node__status canvas-node__status--${data.status}`}
      />
      <strong>{data.title}</strong>
      <span className="canvas-node__meta">{data.assignee}</span>
      {detail === undefined ? null : (
        <span className="canvas-node__meta">{detail}</span>
      )}
      <NodeCost tokens={data.tokens} toolCallCount={data.toolCallCount} />
      {data.retries === 0 ? null : (
        <span className="canvas-node__retries">{data.retries} retries</span>
      )}
      {children}
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
