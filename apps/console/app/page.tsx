/**
 * page.tsx --- console landing page
 *
 * Contains:
 *   Home: points at the live run screen
 */

export default function Home() {
  return (
    <section>
      <h1>Orchestrator overview</h1>
      <p>
        Every run opens on one screen: chat, live task graph, and approvals.
      </p>
      <a href="/run/default">Open the live run</a>
    </section>
  );
}
