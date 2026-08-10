/**
 * ApprovalQueue.tsx --- pending human-in-the-loop approval queue
 *
 * Contains:
 *   ApprovalQueue: lists pending approvals, delegating each decision to a card
 */

"use client";

import { useEffect, useState } from "react";
import { useApprovalShortcuts } from "../hooks/useApprovalShortcuts";
import { ApprovalCard, type Approval } from "./ApprovalCard";

/**
 * Lists pending approvals with approve/reject actions.
 *
 * @returns The approval queue element.
 */
export function ApprovalQueue() {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/approvals/pending`, {
      cache: "no-store",
    })
      .then((res) => {
        if (!res.ok) {
          throw new Error(`approvals fetch failed: ${res.status}`);
        }
        return res.json();
      })
      .then((body) => setApprovals(body.approvals ?? []))
      .catch(() => setApprovals([]))
      .finally(() => setLoading(false));
  }, []);

  const dismiss = (approvalId: string) => {
    setApprovals((prev) =>
      prev.filter((item) => item.approval_id !== approvalId),
    );
  };

  useApprovalShortcuts(approvals, dismiss);

  if (loading) {
    return <p className="queue-loading">Loading approvals…</p>;
  }

  if (approvals.length === 0) {
    return <p className="queue-empty">No pending approvals.</p>;
  }

  return (
    <ul className="approval-queue" aria-live="polite">
      {approvals.map((approval) => (
        <ApprovalCard
          key={approval.approval_id}
          approval={approval}
          onResolve={() => dismiss(approval.approval_id)}
        />
      ))}
    </ul>
  );
}
