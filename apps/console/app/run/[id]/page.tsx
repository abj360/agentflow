/**
 * page.tsx --- unified single-screen view of one orchestration run
 *
 * Contains:
 *   RunPage: hosts the chat, canvas, and raw-log surfaces for one run
 */

"use client";

/**
 * Hosts the chat, canvas, and raw-log surfaces for one run.
 *
 * @param props.params - Route parameters carrying the run identifier.
 * @returns The unified run screen element.
 */
export default function RunPage({ params }: { params: { id: string } }) {
  return (
    <section className="run-screen" data-run={params.id}>
      <header className="run-header">
        <h1>Run {params.id.slice(0, 8)}…</h1>
      </header>
      <aside className="run-chat" aria-label="Run chat" />
      <div className="run-canvas" aria-label="Run canvas" />
      <aside className="run-log" aria-label="Raw trace log" />
    </section>
  );
}
