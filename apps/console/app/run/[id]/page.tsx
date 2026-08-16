/**
 * page.tsx --- unified single-screen view of one orchestration run
 *
 * Contains:
 *   RunHeader: renders the run screen header with the truncated run id
 *   RunPage: hosts the chat, canvas, and raw-log surfaces for one run
 */

"use client";

import { useState } from "react";

import { Canvas } from "../../../components/Canvas";
import { ChatPanel, type ChatMessage } from "../../../components/ChatPanel";
import { TraceViewer } from "../../../components/TraceViewer";
import type { RunViewerTask } from "../../../lib/graph-model";

/**
 * Renders the run screen header with the truncated run identifier.
 *
 * @param props.runId - Identifier of the run currently on screen.
 * @returns The run header element.
 */
function RunHeader({ runId }: { runId: string }) {
  return (
    <header className="run-header">
      <h1>Run {runId.slice(0, 8)}</h1>
      <span className="run-status">live</span>
    </header>
  );
}

/**
 * Hosts the chat, canvas, and raw-log surfaces for one run.
 *
 * @param props.params - Route parameters carrying the run identifier.
 * @returns The unified run screen element.
 */
export default function RunPage({ params }: { params: { id: string } }) {
  const [tasks] = useState<RunViewerTask[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  if (!params.id) {
    return <p className="run-empty">No run selected.</p>;
  }
  return (
    <section className="run-screen" data-run={params.id}>
      <RunHeader runId={params.id} />
      <aside className="run-chat" aria-label="Run chat">
        <ChatPanel
          messages={messages}
          onSend={(instruction) =>
            setMessages((prev) => [
              ...prev,
              { author: "you", text: instruction },
            ])
          }
        />
      </aside>
      <div className="run-canvas" aria-label="Run canvas">
        <Canvas tasks={tasks} />
      </div>
      <aside className="run-log" aria-label="Raw trace log">
        <TraceViewer runId={params.id} />
      </aside>
    </section>
  );
}
