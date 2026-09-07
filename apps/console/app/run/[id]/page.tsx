/**
 * page.tsx --- the single screen one orchestration run is watched from
 *
 * Contains:
 *   appendMessage(): adds one authored turn to a run's conversation
 *   FAILED_TO_START: what the orchestrator says when a run never got going
 *   EMPTY_PROGRESS: the working state shown before a graph exists to count
 *   orchestratorReplies(): turns the run's log lines into orchestrator turns
 *   runProgress(): how far through its graph a run is, while one is running
 *   RunPage: hosts the chat, canvas, and raw-log surfaces for one run
 */

"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { Canvas } from "../../../components/Canvas";
import {
  ChatPanel,
  type ChatMessage,
  type Progress,
} from "../../../components/ChatPanel";
import { NodeInspector } from "../../../components/NodeInspector";
import { PanelDivider } from "../../../components/PanelDivider";
import { ChatSessionList } from "../../../components/ChatSessionList";
import { usePublishTrace } from "../../../components/RunTrace";
import { useApprovalShortcuts } from "../../../hooks/useApprovalShortcuts";
import { usePendingApprovals } from "../../../hooks/usePendingApprovals";
import { useResizablePanel } from "../../../hooks/useResizablePanel";
import { useStickyToggle } from "../../../hooks/useStickyToggle";
import { newRunId, useChatSessions } from "../../../hooks/useChatSessions";
import { useRunGraph } from "../../../hooks/useRunGraph";
import { useWovenTasks } from "../../../hooks/useWovenTasks";
import type { TraceLogEvent } from "../../../hooks/useTraceSocket";
import { startRun } from "../../../lib/api";
import { activeEdges } from "../../../lib/edge-pulse";
import { pairApprovals, type RunViewerTask } from "../../../lib/graph-model";

const FAILED_TO_START = "That instruction did not reach the orchestrator.";

const EMPTY_PROGRESS: Progress = { done: 0, total: 0 };

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
 * Reports how far through its task graph the run is, while one is running.
 *
 * A run is one long request: the team can be working for minutes with nothing
 * to show for it but node badges on a canvas the reviewer may not be looking
 * at. This is what the chat says in the meantime.
 *
 * @param tasks - Tasks the canvas has been told about for this run.
 * @returns progress - Finished and total counts, or null when nothing is running.
 */
function runProgress(tasks: readonly RunViewerTask[]): Progress | null {
  if (tasks.length === 0) {
    return null;
  }
  const settled = tasks.filter(
    (task) => task.status === "done" || task.status === "failed",
  ).length;
  return settled === tasks.length
    ? null
    : { done: settled, total: tasks.length };
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
  const { tasks, pulses, logs, feedback } = useRunGraph(params.id);
  const woven = useWovenTasks(tasks);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [awaiting, setAwaiting] = useState(false);
  const repliesAtSend = useRef(0);
  const { approvals, dismiss } = usePendingApprovals();
  const [focusedTaskId, setFocusedTaskId] = useState<string | null>(null);
  const explorer = useResizablePanel("agentflow.explorer", 240, "left");
  const chat = useResizablePanel("agentflow.chat", 336, "right");
  const sidebar = useStickyToggle("agentflow.sidebar.open", true);
  const chatPanel = useStickyToggle("agentflow.chat.open", true);
  const router = useRouter();
  const { sessions, remember, forget } = useChatSessions();
  usePublishTrace(logs);

  const replies = orchestratorReplies(logs);
  const send = useCallback(
    (instruction: string) => {
      setMessages((prev) => appendMessage(prev, instruction));
      repliesAtSend.current = replies.length;
      setAwaiting(true);
      remember(params.id, instruction.split("\n")[0] ?? instruction);
      startRun(params.id, instruction).catch(() => {
        setAwaiting(false);
        setMessages((prev) => [
          ...prev,
          { author: "orchestrator", text: FAILED_TO_START },
        ]);
      });
    },
    [params.id, remember, replies.length],
  );
  // The coordinator's first reply is what says it heard the goal, so the
  // composer keeps a spinner up until one lands rather than until the run ends.
  const heard = replies.length > repliesAtSend.current;
  const progress = awaiting && !heard ? EMPTY_PROGRESS : runProgress(tasks);
  const focusedTask =
    focusedTaskId === null
      ? null
      : tasks.find((task) => task.id === focusedTaskId) ?? null;
  const focusedApproval =
    focusedTaskId === null
      ? null
      : pairApprovals(tasks, approvals).get(focusedTaskId) ?? null;

  useApprovalShortcuts(focusedApproval?.approval_id ?? null, dismiss);

  if (!params.id) {
    return <p className="run-empty">No run selected.</p>;
  }
  return (
    <section
      className="run-screen"
      data-run={params.id}
      style={{
        gridTemplateColumns: [
          sidebar.on ? `${explorer.width}px auto` : "",
          "minmax(0, 1fr)",
          chatPanel.on ? `auto ${chat.width}px` : "",
        ]
          .filter((column) => column !== "")
          .join(" "),
      }}
    >
      {!sidebar.on ? null : (
        <aside className="run-explorer" aria-label="Chat sessions">
          <ChatSessionList
            sessions={sessions}
            currentId={params.id}
            onOpen={(runId) => router.push(`/run/${runId}`)}
            onNew={() => router.push(`/run/${newRunId()}`)}
            onDelete={(runId) => {
              forget(runId);
              // Deleting the chat you are looking at leaves the screen showing a
              // run the sidebar no longer lists, so it opens a fresh one.
              if (runId === params.id) {
                router.push(`/run/${newRunId()}`);
              }
            }}
            onHide={sidebar.toggle}
          />
        </aside>
      )}
      {!sidebar.on ? null : (
        <PanelDivider
          label="Resize the plan explorer"
          width={explorer.width}
          onResizeStart={explorer.startResize}
          onNudge={explorer.nudge}
        />
      )}
      <div className="run-canvas" aria-label="Run canvas">
        {tasks.length === 0 ||
        focusedTaskId !== null ||
        approvals.length === 0 ? null : (
          <p className="canvas-hint">Select a node to act on it (a / r)</p>
        )}
        <Canvas
          tasks={woven}
          feedback={feedback}
          approvals={approvals}
          onResolve={dismiss}
          activeEdgeIds={activeEdges(pulses, Date.now())}
          onFocusTask={setFocusedTaskId}
        />
        {sidebar.on ? null : (
          <button
            className="sidebar-reveal"
            onClick={sidebar.toggle}
            aria-label="Show the sidebar"
            title="Show the sidebar"
          >
            ›
          </button>
        )}
        {chatPanel.on ? null : (
          <button
            className="chat-reveal"
            onClick={chatPanel.toggle}
            aria-label="Show the chat panel"
            title="Show the chat panel"
          >
            ‹
          </button>
        )}
        {focusedTask === null ? null : (
          <NodeInspector
            task={focusedTask}
            onClose={() => setFocusedTaskId(null)}
          />
        )}
      </div>
      {!chatPanel.on ? null : (
        <PanelDivider
          label="Resize the chat panel"
          width={chat.width}
          onResizeStart={chat.startResize}
          onNudge={chat.nudge}
        />
      )}
      {!chatPanel.on ? null : (
        <aside className="run-chat" aria-label="Run chat">
          <ChatPanel
            messages={[...messages, ...replies]}
            onSend={send}
            onNewSession={() => router.push(`/run/${newRunId()}`)}
            onHide={chatPanel.toggle}
            progress={progress}
          />
        </aside>
      )}
    </section>
  );
}
