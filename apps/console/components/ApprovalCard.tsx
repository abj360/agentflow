/**
 * ApprovalCard.tsx --- one approval request, rendered inside its canvas node
 *
 * Contains:
 *   ApprovalCard: shows an approval request with approve/reject buttons
 */

"use client";

import {
  useApprovalDecision,
  type ApprovalDecision,
} from "../hooks/useApprovalDecision";
import type { Approval } from "../lib/api";

/**
 * Shows an approval request with approve/reject buttons.
 *
 * @param props.approval - The approval request to display.
 * @param props.onResolve - Called with the recorded decision once the API accepts it.
 * @returns The approval card element.
 */
export function ApprovalCard({
  approval,
  onResolve,
}: Readonly<{
  approval: Approval;
  onResolve: (status: ApprovalDecision) => void;
}>) {
  const { decide, pending, error } = useApprovalDecision(
    approval.approval_id,
    onResolve,
  );

  return (
    <div className="approval-inline" role="group" aria-label="Approval">
      <header>
        <strong title={approval.tool_name}>
          {approval.tool_name || "unnamed tool"}
        </strong>
        <span className="approval-trace">
          trace {approval.trace_id.slice(0, 8)}…
        </span>
      </header>
      <footer>
        <button
          className="approve"
          disabled={pending}
          aria-label={`Approve ${approval.tool_name}`}
          onClick={() => decide("approved")}
        >
          Approve
        </button>
        <button
          className="reject"
          disabled={pending}
          aria-label={`Reject ${approval.tool_name}`}
          onClick={() => decide("rejected")}
        >
          Reject
        </button>
      </footer>
      {error === null ? null : (
        <p className="approval-error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
