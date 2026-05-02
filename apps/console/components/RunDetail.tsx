#!/usr/bin/env ts-node
/**
 * RunDetail.tsx --- drill-down view of one orchestration run
 *
 * Contains:
 *   RunDetail: loads and renders one run's audit events
 */

"use client";

import { useEffect, useState } from "react";
import { fetchTrace, type TraceResponse } from "../../lib/api";

/**
 * Loads and renders one run's audit events.
 *
 * @param props.runId - Identifier of the run to drill into.
 * @returns The run detail element.
 */
export function RunDetail({ runId }: { runId: string }) {
  const [trace, setTrace] = useState<TraceResponse | null>(null);

  useEffect(() => {
    fetchTrace(runId).then(setTrace);
  }, [runId]);

  if (!trace) {
    return <p className="run-loading">Loading run…</p>;
  }

  return (
    <section>
      <h1>Run detail — {runId.slice(0, 8)}</h1>
      <p>
        {trace.event_count} events — chain {trace.chain_valid ? "valid" : "invalid"}
      </p>
      <ol className="trace-list">
        {trace.events.map((event, index) => (
          <li key={index} className="trace-event">
            <span className="trace-kind">{event.kind}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}
