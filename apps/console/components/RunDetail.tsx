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
    let cancelled = false;  // guard against state set after unmount
    fetchTrace(runId).then((data) => {
      if (!cancelled) {
        setTrace(data);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [runId]);

  if (!trace) {
    return (
      <p className="run-loading" role="status">
        Loading run…
      </p>
    );
  }

  return (
    <section>
      <h1>Run {runId.slice(0, 8)}…</h1>
      <p>
        {trace.event_count} events — chain{' '}
        {trace.chain_valid ? "valid" : "invalid"}
      </p>
      <ol className="trace-list" aria-label="Run events">
        {trace.events.map((event, index) => (
          <li key={index} className="trace-event">
            <span className="trace-kind">{event.kind}</span>
            <code title={event.event_hash}>
              {event.event_hash.slice(0, 12)}…
            </code>
          </li>
        ))}
      </ol>
    </section>
  );
}
