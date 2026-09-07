/**
 * NodeInspector.tsx --- everything one task node knows, opened from the canvas
 *
 * Contains:
 *   STATUS_LABELS: how each lifecycle state is written for a reader
 *   duration(): renders how long a task took, once it has taken any
 *   Field: one labelled value in the inspector's grid
 *   NodeInspector: shows one task's evidence beside the graph
 */

"use client";

import type { ReactNode } from "react";

import { speciesFor, type RunViewerTask } from "../lib/graph-model";
import { Markdown } from "./Markdown";

const STATUS_LABELS: Readonly<Record<string, string>> = {
  pending: "Pending",
  running: "Running",
  "awaiting-approval": "Awaiting approval",
  done: "Completed",
  failed: "Failed",
};

/**
 * Renders how long a task took, once it has taken any measurable time.
 *
 * @param task - The task whose clock is being read.
 * @returns spent - A short duration, or a dash while the task has not settled.
 */
export function duration(task: Readonly<RunViewerTask>): string {
  if (task.startedAt === null || task.finishedAt === null) {
    return "—";
  }
  const seconds = task.finishedAt - task.startedAt;
  return seconds < 60
    ? `${seconds.toFixed(1)} s`
    : `${(seconds / 60).toFixed(1)} min`;
}

/**
 * Renders one labelled value in the inspector's grid.
 *
 * @param props.label - What the value is.
 * @param props.children - The value itself.
 * @returns The field element.
 */
function Field({
  label,
  children,
}: Readonly<{ label: string; children: ReactNode }>) {
  return (
    <div className="inspector__field">
      <p className="inspector__label">{label}</p>
      <p className="inspector__value">{children}</p>
    </div>
  );
}

/**
 * Shows one task's evidence beside the graph it belongs to.
 *
 * The canvas can only carry a title and a status without becoming unreadable,
 * so everything else a run records about a task lives here and is opened on
 * demand rather than crowded onto the node.
 *
 * @param props.task - The task the reviewer selected.
 * @param props.onClose - Called when the reviewer dismisses the inspector.
 * @returns The inspector element.
 */
export function NodeInspector({
  task,
  onClose,
}: Readonly<{ task: Readonly<RunViewerTask>; onClose: () => void }>) {
  return (
    <aside className="inspector" aria-label="Task detail">
      <header className="inspector__head">
        <p className="inspector__eyebrow">Task evidence</p>
        <button
          className="inspector__close"
          onClick={onClose}
          aria-label="Close task detail"
        >
          ×
        </button>
      </header>
      <h2 className="inspector__title">{task.title}</h2>
      <p className={`inspector__status inspector__status--${task.status}`}>
        {STATUS_LABELS[task.status] ?? task.status}
      </p>

      <div className="inspector__grid">
        <Field label="Agent">{task.assignee}</Field>
        <Field label="Kind">{speciesFor(task)}</Field>
        <Field label="Task">{task.id}</Field>
        <Field label="Duration">{duration(task)}</Field>
        <Field label="Tokens">{task.tokens.toLocaleString()}</Field>
        <Field label="Tool calls">{task.toolCallCount}</Field>
        <Field label="Retries">{task.retries}</Field>
        <Field label="Waits on">
          {task.dependsOn.length === 0 ? "nothing" : task.dependsOn.join(", ")}
        </Field>
      </div>

      {task.output === undefined || task.output === "" ? null : (
        <section className="inspector__output">
          <p className="inspector__label">Output</p>
          <Markdown text={task.output} />
        </section>
      )}
    </aside>
  );
}
