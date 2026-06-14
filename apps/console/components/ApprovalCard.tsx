#!/usr/bin/env ts-node
/**
 * ApprovalCard.tsx --- one pending approval request card
 *
 * Contains:
 *   ApprovalCard: shows an approval request with approve/reject buttons
 */

"use client";

import type { Approval } from "./ApprovalQueue";


/**
 * Shows an approval request with approve/reject buttons.
 *
 * @param props.approval - The approval request to display.
 * @returns The approval card element.
 */
export function ApprovalCard({
  approval,
  onResolve,
}: Readonly<{
  approval: Approval;
  onResolve: (status: string) => void;
}>) {
  return (
    <li className="approval-card">
      <header>
        <strong title={approval.tool_name}>{approval.tool_name}</strong>
        <span className="approval-trace">{approval.trace_id}</span>
      </header>
      <footer>
        <button
          className="approve"
          aria-label={`Approve ${approval.tool_name}`}
          onClick={() => onResolve("approved")}
        >
          Approve
        </button>
        <button
          className="reject"
          aria-label={`Reject ${approval.tool_name}`}
          onClick={() => onResolve("rejected")}
        >
          Reject
        </button>
      </footer>
    </li>
  );
}
