#!/usr/bin/env ts-node
/**
 * ApprovalQueue.tsx --- pending human-in-the-loop approval queue
 *
 * Contains:
 *   ApprovalQueue: lists pending approvals with approve/reject actions
 *   Approval: one pending approval request
 */

"use client";

import { useEffect, useState } from "react";
import { ApprovalCard } from "./ApprovalCard";

export interface Approval {
  approval_id: string;
  trace_id: string;
  tool_name: string;
  status: string;
}

/**
 * Lists pending approvals with approve/reject actions.
 *
 * @returns The approval queue element.
 */
export function ApprovalQueue() {
  const [approvals, setApprovals] = useState<Approval[]>([]);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/approvals/pending`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`approvals fetch failed: ${res.status}`);
        }
        return res.json();
      })
      .then((body) => setApprovals(body.approvals ?? []))
      .catch(() => setApprovals([]));
  }, []);

  const resolve = async (approvalId: string, status: string) => {
    await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/approvals/${approvalId}/resolve`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      }
    );
    setApprovals((prev) =>
      prev.filter((item) => item.approval_id !== approvalId)  // drop resolved card
    );
  };

  if (approvals.length === 0) {
    return <p className="queue-empty">No pending approvals.</p>;
  }

  return (
    <ul className="approval-queue" aria-live="polite">
      {approvals.map((approval) => (
        <ApprovalCard
          key={approval.approval_id}
          approval={approval}
          onResolve={(status) => resolve(approval.approval_id, status)}
        />
      ))}
    </ul>
  );
}
