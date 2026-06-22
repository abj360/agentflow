#!/usr/bin/env ts-node
/**
 * page.tsx --- live traces page
 *
 * Contains:
 *   TracesPage: hosts the live trace viewer
 */

"use client";

import { useState } from "react";
import { TraceViewer } from "../../components/TraceViewer";

export default function TracesPage() {
  const [runId, setRunId] = useState("default");

  return (
    <section>
      <h1>Live trace viewer</h1>
      <label>
        Run id
        <input
          aria-label="Run id"
          value={runId}
          onChange={(e) => setRunId(e.target.value)}
        />
      </label>
      <TraceViewer runId={runId} />
    </section>
  );
}
