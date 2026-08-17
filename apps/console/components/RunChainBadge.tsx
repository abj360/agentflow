/**
 * RunChainBadge.tsx --- audit-chain verdict for the run currently on screen
 *
 * Contains:
 *   RunChainBadge: reports whether the run's hash-chained audit trail verifies
 */

"use client";

import { useEffect, useState } from "react";

import { fetchTrace, type TraceResponse } from "../lib/api";

/**
 * Reports whether the run's hash-chained audit trail still verifies.
 *
 * @param props.runId - Identifier of the run on screen.
 * @returns The chain verdict element, or nothing until the trace loads.
 */
export function RunChainBadge({ runId }: Readonly<{ runId: string }>) {
  const [trace, setTrace] = useState<TraceResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchTrace(runId)
      .then((loaded) => {
        if (!cancelled) {
          setTrace(loaded);
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [runId]);

  if (trace === null) {
    return null;
  }

  return (
    <span className="run-chain" title={`${trace.event_count} audited events`}>
      chain {trace.chain_valid ? "verified" : "broken"}
    </span>
  );
}
