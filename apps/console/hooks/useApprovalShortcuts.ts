/**
 * useApprovalShortcuts.ts --- keyboard shortcuts for approving and rejecting
 *
 * Contains:
 *   APPROVE_KEY: single press that approves the approval a reviewer is looking at
 *   REJECT_KEY: single press that rejects the approval a reviewer is looking at
 *   useApprovalShortcuts(): binds the approve and reject shortcuts for the queue
 */

"use client";

import { useEffect } from "react";

import type { Approval } from "../components/ApprovalCard";

export const APPROVE_KEY = "a";
export const REJECT_KEY = "r";

/**
 * Binds the approve and reject shortcuts while approvals are pending.
 *
 * @param approvals - Pending approvals in the order the queue lists them.
 * @param onDecide - Called with the approval id and the decision the key maps to.
 */
export function useApprovalShortcuts(
  approvals: Approval[],
  onDecide: (approvalId: string, status: string) => void,
): void {
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const [first] = approvals;
      if (first === undefined) {
        return;
      }
      if (event.key === APPROVE_KEY) {
        onDecide(first.approval_id, "approved");
      }
      if (event.key === REJECT_KEY) {
        onDecide(first.approval_id, "rejected");
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [approvals, onDecide]);
}
