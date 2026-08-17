/**
 * page.tsx --- unified single-screen view of one orchestration run
 *
 * Contains:
 *   RunHeader: renders the run screen header with the truncated run id
 *   appendMessage(): adds one authored turn to a run's conversation
 *   RunPage: hosts the chat, canvas, and raw-log surfaces for one run
 */

"use client";

import { useState } from "react";

import { usePendingApprovals } from "../../../hooks/usePendingApprovals";
import { Canvas } from "../../../components/Canvas";
import { RunChainBadge } from "../../../components/RunChainBadge";
import { ChatPanel, type ChatMessage } from "../../../components/ChatPanel";
import { TraceViewer } from "../../../components/TraceViewer";
import { useRunGraph } from "../../../hooks/useRunGraph";

/**
 * Renders the run screen header with the truncated run identifier.
 *
 * @param props.runId - Identifier of the run currently on screen.
 * @returns The run header element.
 */
function RunHeader({ runId }: Readonly<{ runId: string }>) {
  return (
    <header className="run-header">
      <h1>Run {runId.slice(0, 8)}</h1>
      <span className="run-status">live</span>
      <RunChainBadge runId={runId} />
    </header>
  );
}

/**
 * Adds one authored turn to a run's conversation.
 *
 * @param messages - Turns exchanged so far.
 * @param text - The instruction the reviewer just sent.
 * @returns conversation - The turns with the new instruction appended.
 */
function appendMessage(
  messages: readonly ChatMessage[],
  text: string,
): ChatMessage[] {
  return [...messages, { author: "you", text }];
}

/**
 * Hosts the chat, canvas, and raw-log surfaces for one run.
 *
 * @param props.params - Route parameters carrying the run identifier.
 * @returns The unified run screen element.
 */
export default function RunPage({
  params,
}: Readonly<{ params: { id: string } }>) {
  // Hooks cannot sit behind the guard below, so the empty run id is handled
  // by the socket refusing to connect rather than by an early return.
  const { tasks } = useRunGraph(params.id);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const { approvals, dismiss } = usePendingApprovals();

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
            setMessages((prev) => appendMessage(prev, instruction))
          }
        />
      </aside>
      <div className="run-canvas" aria-label="Run canvas">
        <Canvas tasks={tasks} approvals={approvals} onResolve={dismiss} />
      </div>
      <aside className="run-log" aria-label="Raw trace log">
        <TraceViewer runId={params.id} />
      </aside>
    </section>
  );
}
