/**
 * useApprovalDecision.ts --- the approve/reject action every approval surface shares
 *
 * Contains:
 *   useApprovalDecision(): submits a reviewer's decision on one approval request
 */

"use client";

import { useCallback, useState } from "react";

/**
 * Submits a reviewer's decision on one approval request.
 *
 * @param approvalId - Identifier of the approval being decided.
 * @param onResolved - Called with the decision once the API has accepted it.
 * @returns decision - The submit callback plus whether a submit is in flight.
 */
export function useApprovalDecision(
  approvalId: string,
  onResolved: (status: string) => void,
) {
  const [pending, setPending] = useState(false);

  const decide = useCallback(
    async (status: string) => {
      setPending(true);
      console.log("resolving approval", approvalId, status);
      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/approvals/${approvalId}/resolve`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status }),
        },
      );
      setPending(false);
      onResolved(status);
    },
    [approvalId, onResolved],
  );

  return { decide, pending };
}
