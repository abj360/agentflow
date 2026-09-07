/**
 * ChatPanel.tsx --- instruction input and the orchestrator's replies
 *
 * Contains:
 *   ChatMessage: one turn in a run's conversation, from either side
 *   Progress: how far through its task graph a run currently is
 *   PLANNING_AFTER_MS: when the pre-plan label moves from reasoning to planning
 *   Working: says the team heard the goal, then how far it has got
 *   ChatPanel: sends instructions into a run and lists the replies coming back
 */

"use client";

import { useEffect, useState } from "react";

import { ChatEmptyState } from "./ChatEmptyState";
import { Markdown } from "./Markdown";
import { ModelPicker } from "./ModelPicker";

export interface ChatMessage {
  readonly author: "you" | "orchestrator";
  readonly text: string;
}

export interface Progress {
  readonly done: number;
  readonly total: number;
}

const PLANNING_AFTER_MS = 5000;

/**
 * Says what the team is doing, before and during a run.
 *
 * Before a graph exists there is nothing to count, so the label reports the
 * stage instead: the coordinator reasons about the goal first and only then
 * has a plan to hand over.
 *
 * @param props.progress - How far through its graph the run is.
 * @returns The working-state element.
 */
function Working({ progress }: Readonly<{ progress: Progress }>) {
  const [planning, setPlanning] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setPlanning(true), PLANNING_AFTER_MS);
    return () => clearTimeout(timer);
  }, []);

  const label =
    progress.total > 0
      ? `Running — ${progress.done} of ${progress.total} done`
      : planning
        ? "Planning…"
        : "Reasoning…";
  return (
    <p className="chat-working" role="status">
      <span className="chat-working__spinner" aria-hidden="true" />
      {label}
    </p>
  );
}

/**
 * Sends instructions into a run and lists the replies streaming back.
 *
 * @param props.messages - Conversation turns received for this run so far.
 * @param props.onSend - Called with an instruction the reviewer wants to send.
 * @param props.onNewSession - Called when the reviewer wants a fresh chat.
 * @param props.onHide - Called when the reviewer wants the panel out of the way.
 * @param props.progress - How far through its graph the run is, while one is running.
 * @returns The chat panel element.
 */
export function ChatPanel({
  messages,
  onSend,
  onNewSession,
  onHide,
  progress,
}: Readonly<{
  messages: readonly ChatMessage[];
  onSend: (instruction: string) => void;
  onNewSession: () => void;
  onHide: () => void;
  progress: Progress | null;
}>) {
  const [draft, setDraft] = useState("");

  const send = () => {
    const instruction = draft.trim();
    if (instruction.length === 0) {
      return;
    }
    // The composer keeps focus after a send, so the reviewer can keep typing
    // without reaching for the mouse between instructions.
    onSend(instruction);
    setDraft("");
  };

  return (
    <div className="chat-panel">
      <div className="chat-panel__head">
        <button
          className="chat-panel__hide"
          onClick={onHide}
          aria-label="Hide the chat panel"
          title="Hide the chat panel"
        >
          ›
        </button>
      </div>
      {messages.length > 0 ? null : <ChatEmptyState />}
      <ol
        className="chat-log"
        aria-live="polite"
        hidden={messages.length === 0}
      >
        {messages.map((message, index) => (
          <li
            key={index}
            className={`chat-message chat-message--${message.author}`}
          >
            <span className="chat-author">
              {message.author === "you" ? "You" : "Agentflow"}
            </span>
            <Markdown text={message.text} />
          </li>
        ))}
      </ol>
      {progress === null ? null : <Working progress={progress} />}
      <form
        className="chat-composer"
        onSubmit={(event) => {
          event.preventDefault();
          send();
        }}
      >
        <textarea
          aria-label="Instruction"
          maxLength={2000}
          rows={3}
          placeholder="Describe a goal"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              send();
            }
          }}
        />
        <div className="chat-composer__bar">
          <button
            className="chat-composer__new"
            type="button"
            aria-label="New chat"
            title="New chat"
            onClick={onNewSession}
          >
            +
          </button>
          <ModelPicker />
          <button
            className="chat-composer__send"
            type="submit"
            aria-label="Send"
            disabled={draft.trim().length === 0}
          >
            <svg
              width="15"
              height="15"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M12 19V5M5 12l7-7 7 7" />
            </svg>
          </button>
        </div>
      </form>
    </div>
  );
}
