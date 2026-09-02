/**
 * page.tsx --- the single screen one orchestration run is watched from
 *
 * Contains:
 *   RunHeader: renders the run screen header with the truncated run id
 *   appendMessage(): adds one authored turn to a run's conversation
 *   orchestratorReplies(): turns the run's log lines into orchestrator turns
 *   RunPage: hosts the chat, canvas, and raw-log surfaces for one run
 */

"use client";

import { useState } from "react";

import { Canvas } from "../../../components/Canvas";
import { ChatPanel, type ChatMessage } from "../../../components/ChatPanel";
import { RunChainBadge } from "../../../components/RunChainBadge";
import { TraceViewer } from "../../../components/TraceViewer";
import { useApprovalShortcuts } from "../../../hooks/useApprovalShortcuts";
import { usePendingApprovals } from "../../../hooks/usePendingApprovals";
import { useRunGraph } from "../../../hooks/useRunGraph";
import type { TraceLogEvent } from "../../../hooks/useTraceSocket";
import { activeEdges } from "../../../lib/edge-pulse";
import { pairApprovals } from "../../../lib/graph-model";

/**
 * Renders the run screen header with the truncated run identifier.
 *
 * @param props.runId - Identifier of the run currently on screen.
 * @param props.isLive - Whether the trace socket is currently connected.
 * @returns The run header element.
 */
function RunHeader({
  runId,
  isLive,
}: Readonly<{ runId: string; isLive: boolean }>) {
  return (
    <header className="run-header">
      <h1>Run {runId.slice(0, 8)}</h1>
      <span className="run-liveness">{isLive ? "live" : "offline"}</span>
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
 * Turns the run's log lines into the orchestrator's side of the conversation.
 *
 * @param logs - Raw log lines received for this run so far.
 * @returns replies - One turn per line the orchestrator addressed to the user.
 */
function orchestratorReplies(logs: readonly TraceLogEvent[]): ChatMessage[] {
  return logs
    .filter((log) => log.kind === "orchestrator_message")
    .map((log) => ({
      author: "orchestrator" as const,
      text: String(log.payload.text ?? ""),
    }))
    .filter((message) => message.text.length > 0);
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
  // Hooks cannot sit behind the guard below, so an empty run id is handled by
  // the socket refusing to connect rather than by an early return.
  const { tasks, pulses, logs, isLive } = useRunGraph(params.id);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const { approvals, dismiss } = usePendingApprovals();
  const [focusedTaskId, setFocusedTaskId] = useState<string | null>(null);
  const focusedApproval =
    focusedTaskId === null
      ? null
      : pairApprovals(tasks, approvals).get(focusedTaskId) ?? null;

  useApprovalShortcuts(focusedApproval?.approval_id ?? null, dismiss);

  if (!params.id) {
    return <p className="run-empty">No run selected.</p>;
  }
  return (
    <section className="run-screen" data-run={params.id}>
      <RunHeader runId={params.id} isLive={isLive} />
      <aside className="run-chat" aria-label="Run chat">
        <ChatPanel
          messages={[...messages, ...orchestratorReplies(logs)]}
          onSend={(instruction) =>
            setMessages((prev) => appendMessage(prev, instruction))
          }
        />
      </aside>
      <div className="run-canvas" aria-label="Run canvas">
        {tasks.length === 0 ||
        focusedTaskId !== null ||
        approvals.length === 0 ? null : (
          <p className="canvas-hint">Select a node to act on it (a / r)</p>
        )}
        <Canvas
          tasks={tasks}
          approvals={approvals}
          onResolve={dismiss}
          activeEdgeIds={activeEdges(pulses, Date.now())}
          onFocusTask={setFocusedTaskId}
        />
      </div>
      <aside className="run-log" aria-label="Raw trace log">
        <TraceViewer events={logs} />
      </aside>
    </section>
  );
}
