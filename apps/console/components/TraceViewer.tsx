/**
 * TraceViewer.tsx --- raw trace log, behind a debug toggle under the canvas
 *
 * Contains:
 *   MAX_VISIBLE_LINES: how many log lines the panel keeps on screen at once
 *   TraceViewer: renders a run's raw log events behind a disclosure toggle
 *   TraceLogList: renders the ordered list of raw log lines
 *   TraceTruncationNote: says how much of a long log the panel is showing
 *   TraceEmptyState: renders the empty state shown before the first event arrives
 *   TraceEventCount: renders the running event count badge
 */

"use client";

import { useState } from "react";

const MAX_VISIBLE_LINES = 200;

import type { TraceLogEvent } from "../hooks/useTraceSocket";

/**
 * Renders a run's raw log events behind a disclosure toggle.
 *
 * @param props.events - Raw log lines the run screen already receives.
 * @returns The raw log panel element.
 */
export function TraceViewer({
  events,
}: Readonly<{ events: readonly TraceLogEvent[] }>) {
  const [isRawLogOpen, setRawLogOpen] = useState(false);
  const recent =
    events.length > MAX_VISIBLE_LINES
      ? events.slice(-MAX_VISIBLE_LINES)
      : events;

  return (
    <div className="trace-panel">
      <button
        className="trace-toggle"
        aria-expanded={isRawLogOpen}
        onClick={() => setRawLogOpen(!isRawLogOpen)}
      >
        Raw trace log <TraceEventCount count={events.length} />
      </button>
      {!isRawLogOpen ? null : (
        <TraceTruncationNote total={events.length} />
      )}
      {!isRawLogOpen || events.length > 0 ? null : <TraceEmptyState />}
      {!isRawLogOpen || events.length === 0 ? null : (
        <TraceLogList events={recent} />
      )}
    </div>
  );
}

/**
 * Says how much of a long log the panel is currently showing.
 *
 * @param props.total - Log lines received for this run so far.
 * @returns The truncation note, or nothing while the whole log fits.
 */
function TraceTruncationNote({ total }: Readonly<{ total: number }>) {
  if (total <= MAX_VISIBLE_LINES) {
    return null;
  }
  return (
    <p className="trace-truncated">
      showing the last {MAX_VISIBLE_LINES} of {total} lines
    </p>
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
}: Readonly<{ events: readonly TraceLogEvent[] }>) {
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
export function TraceEventCount({ count }: Readonly<{ count: number }>) {
  return (
    <span className="trace-count">
      {count} {count === 1 ? "event" : "events"}
    </span>
  );
}
