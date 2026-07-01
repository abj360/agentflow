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

  if (events.length === 0) {
    return <TraceEmptyState />;
  }

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


/**
 * Renders the empty state shown before the first event arrives.
 *
 * @returns The empty-state element.
 */
export function TraceEmptyState() {
  return <p className="trace-empty">Waiting for trace events…</p>;
}


/**
 * Renders the running event count badge.
 *
 * @param props.count - Number of events received so far.
 * @returns The count badge element.
 */
export function TraceEventCount({ count }: { count: number }) {
  return <span className="trace-count">{count} events</span>;
}
