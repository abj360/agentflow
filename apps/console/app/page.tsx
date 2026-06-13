#!/usr/bin/env ts-node
/**
 * page.tsx --- console landing page
 *
 * Contains:
 *   Home: overview page linking to traces and approvals
 */

export default function Home() {
  return (
    <section>
      <h1>Orchestrator overview</h1>
      <p>Live view of orchestration runs, audit traces, and pending approvals.</p>
      <ul>
        <li>
          <a href="/traces">Live traces</a> — watch runs as they happen
        </li>
        <li>
          <a href="/approvals">Approval queue</a>
        </li>
      </ul>
    </section>
  );
}
