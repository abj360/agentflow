#!/usr/bin/env ts-node
/**
 * TraceViewer.tsx --- live trace event list for one run
 *
 * Contains:
 *   TraceViewer: renders streaming trace events for a run
 */

"use client";

import { useTraceSocket } from "../hooks/useTraceSocket";

/**
 * Renders streaming trace events for a run.
 *
 * @param props.runId - Identifier of the run to watch.
 * @returns The live event list element.
 */
export function TraceViewer({ runId }: { runId: string }) {
  const events = useTraceSocket(runId);

  return (
    <ol className="trace-list">
      {events.map((event, index) => (
        <li key={`${event.kind}-${index}`} className={`trace-event trace-${event.kind}`}>
          <span className="trace-role">{event.role}</span>
          <span className="trace-kind">{event.kind}</span>
        </li>
      ))}
    </ol>
  );
}
