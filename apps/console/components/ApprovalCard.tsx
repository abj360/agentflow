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
export function ApprovalCard({ approval }: { approval: Approval }) {
  return (
    <li className="approval-card">
      <header>
        <strong>{approval.tool_name}</strong>
        <span className="approval-trace">{approval.trace_id}</span>
      </header>
      <footer>
        <button className="approve">Approve</button>
        <button className="reject">Reject</button>
      </footer>
    </li>
  );
}
