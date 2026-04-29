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
      .then((res) => res.json())
      .then((body) => setApprovals(body.approvals ?? []));
  }, []);

  return (
    <ul className="approval-queue">
      {approvals.map((approval) => (
        <ApprovalCard key={approval.approval_id} approval={approval} />
      ))}
    </ul>
  );
}
