/**
 * TraceViewer.tsx --- raw trace log, tucked behind a debug toggle under the canvas
 *
 * Contains:
 *   TraceViewer: renders a run's raw log events behind a disclosure toggle
 *   TraceLogList: renders the ordered list of raw log lines
 *   TraceEmptyState: renders the empty state shown before the first event arrives
 *   TraceEventCount: renders the running event count badge
 */

"use client";

import { useState } from "react";

import {
  isLogEvent,
  useTraceSocket,
  type TraceLogEvent,
} from "../hooks/useTraceSocket";

/**
 * Renders a run's raw log events behind a disclosure toggle.
 *
 * @param props.runId - Identifier of the run to watch.
 * @returns The raw log panel element.
 */
export function TraceViewer({ runId }: Readonly<{ runId: string }>) {
  const [isRawLogOpen, setRawLogOpen] = useState(false);
  const events = useTraceSocket(runId).filter(isLogEvent);

  return (
    <div className="trace-panel">
      <button
        className="trace-toggle"
        aria-expanded={isRawLogOpen}
        onClick={() => setRawLogOpen(!isRawLogOpen)}
      >
        Raw trace log <TraceEventCount count={events.length} />
      </button>
      {!isRawLogOpen || events.length > 0 ? null : <TraceEmptyState />}
      {!isRawLogOpen || events.length === 0 ? null : (
        <TraceLogList events={events} />
      )}
    </div>
  );
}

/**
 * Renders the ordered list of raw log lines.
 *
 * @param props.events - Log events received for this run so far.
 * @returns The raw log list element.
 */
function TraceLogList({
  events,
}: {
  events: readonly TraceLogEvent[];
}) {
  return (
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
