/**
 * ApprovalNode.tsx --- task node species for a step waiting on a human decision
 *
 * Contains:
 *   ApprovalNode: renders a task that is paused for a reviewer's decision
 */

"use client";

import type { NodeProps } from "reactflow";

import { TaskNode, type TaskNodeData } from "./TaskNode";

/**
 * Renders a task that is paused waiting for a reviewer's decision.
 *
 * @param props - Node props React Flow passes straight through to the shell.
 * @returns The approval node element.
 */
export function ApprovalNode(props: NodeProps<TaskNodeData>) {
  return <TaskNode {...props} species="approval" detail="Awaiting decision" />;
}
