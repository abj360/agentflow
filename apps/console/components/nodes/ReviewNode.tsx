/**
 * ReviewNode.tsx --- the node species a review pass is drawn as
 *
 * Contains:
 *   ReviewNode: renders a critic's task inside the shared task node shell
 */

"use client";

import type { NodeProps } from "reactflow";

import { TaskNode, type TaskNodeData } from "./TaskNode";

/**
 * Renders a critic's task inside the shared task node shell.
 *
 * @param props - Node props React Flow passes straight through to the shell.
 * @returns The review node element.
 */
export function ReviewNode(props: NodeProps<TaskNodeData>) {
  return <TaskNode {...props} species="review" />;
}
