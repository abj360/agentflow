/**
 * usePendingApprovals.ts --- the approval requests a run is currently blocked on
 *
 * Contains:
 *   usePendingApprovals(): loads pending approvals and drops them once decided
 */

"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchPendingApprovals, type Approval } from "../lib/api";

/**
 * Loads the approvals waiting on a reviewer and drops each one as it is decided.
 *
 * @returns pending - The waiting approvals plus the callback that clears one.
 */
export function usePendingApprovals() {
  const [approvals, setApprovals] = useState<Approval[]>([]);

  useEffect(() => {
    let cancelled = false;
    fetchPendingApprovals()
      .then((loaded) => {
        if (!cancelled) {
          setApprovals(loaded);
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  const dismiss = useCallback((approvalId: string) => {
    setApprovals((prev) =>
      prev.filter((approval) => approval.approval_id !== approvalId),
    );
  }, []);

  return { approvals, dismiss };
}
