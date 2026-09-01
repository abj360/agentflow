/**
 * ApprovalNode.tsx --- task node species for a step waiting on a human decision
 *
 * Contains:
 *   ApprovalNode: renders a paused task, expanding into its approval decision
 */

"use client";

import type { NodeProps } from "reactflow";

import { ApprovalCard } from "../ApprovalCard";
import { TaskNode, type TaskNodeData } from "./TaskNode";

/**
 * Renders a task that is paused waiting for a reviewer's decision.
 *
 * @param props - Node props React Flow passes through, carrying any approval.
 * @returns The approval node element.
 */
export function ApprovalNode(props: NodeProps<TaskNodeData>) {
  const { approval, onResolve } = props.data;

  if (approval === undefined || onResolve === undefined) {
    // The plan can mark a task as waiting before the approvals API has caught
    // up, so the node has to read as paused with no decision to offer yet.
    return (
      <TaskNode {...props} species="approval" detail="Awaiting approval" />
    );
  }

  return (
    <TaskNode {...props} species="approval">
      <ApprovalCard
        approval={approval}
        onResolve={() => onResolve(approval.approval_id)}
      />
    </TaskNode>
  );
}
