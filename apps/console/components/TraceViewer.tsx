/**
 * TraceViewer.tsx --- raw trace log, tucked behind a debug toggle under the canvas
 *
 * Contains:
 *   TraceViewer: renders a run's raw log events behind a disclosure toggle
 *   TraceEmptyState: renders the empty state shown before the first event arrives
 *   TraceEventCount: renders the running event count badge
 */

"use client";

import { useState } from "react";

import { isLogEvent, useTraceSocket } from "../hooks/useTraceSocket";

/**
 * Renders a run's raw log events behind a disclosure toggle.
 *
 * @param props.runId - Identifier of the run to watch.
 * @returns The raw log panel element.
 */
export function TraceViewer({ runId }: { runId: string }) {
  const [open, setOpen] = useState(false);
  const events = useTraceSocket(runId).filter(isLogEvent);

  return (
    <div className="trace-panel">
      <button
        className="trace-toggle"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        Raw trace log <TraceEventCount count={events.length} />
      </button>
      {!open ? null : (
        <ol className="trace-list">
          {events.map((event, index) => (
            <li
              key={`${event.kind}-${index}`}
              className={`trace-event trace-${event.kind}`}
            >
              <span className="trace-role">{event.role}</span>
              <span className="trace-kind">{event.kind}</span>
            </li>
          ))}
        </ol>
      )}
    </div>
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
