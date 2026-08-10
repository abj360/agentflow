/**
 * useApprovalDecision.ts --- the approve/reject action every approval surface shares
 *
 * Contains:
 *   ApprovalDecision: the two outcomes a reviewer can record
 *   useApprovalDecision(): submits a reviewer's decision on one approval request
 */

"use client";

import { useCallback, useState } from "react";

import { resolveApproval } from "../lib/api";

export type ApprovalDecision = "approved" | "rejected";

/**
 * Submits a reviewer's decision on one approval request.
 *
 * @param approvalId - Identifier of the approval being decided.
 * @param onResolved - Called with the decision once the API has accepted it.
 * @returns decision - The submit callback, the in-flight flag, and the last error.
 */
export function useApprovalDecision(
  approvalId: string,
  onResolved: (status: ApprovalDecision) => void,
) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const decide = useCallback(
    async (status: ApprovalDecision) => {
      if (!approvalId) {
        return;
      }
      setPending(true);
      const accepted = await resolveApproval(approvalId, status);
      setPending(false);
      if (!accepted) {
        setError("The API rejected that decision. Try again.");
        return;
      }
      setError(null);
      onResolved(status);
    },
    [approvalId, onResolved],
  );

  return { decide, pending, error };
}
