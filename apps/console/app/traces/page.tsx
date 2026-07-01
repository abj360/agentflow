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
      <h1>Live traces</h1>
      <label>
        Run id
        <input
          aria-label="Run id to stream"
          placeholder="run id"
          value={runId}
          onChange={(e) => setRunId(e.target.value)}
        />
      </label>
      <TraceViewer runId={runId} />
    </section>
  );
}
