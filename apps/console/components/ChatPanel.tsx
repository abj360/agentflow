/**
 * ChatPanel.tsx --- instruction input and the orchestrator's replies
 *
 * Contains:
 *   ChatMessage: one turn in a run's conversation
 *   ChatPanel: sends instructions into a run and lists the replies coming back
 */

"use client";

import { useState } from "react";

export interface ChatMessage {
  readonly author: "you" | "orchestrator";
  readonly text: string;
}

/**
 * Sends instructions into a run and lists the replies streaming back.
 *
 * @param props.messages - Conversation turns received for this run so far.
 * @param props.onSend - Called with an instruction the reviewer wants to send.
 * @returns The chat panel element.
 */
export function ChatPanel({
  messages,
  onSend,
}: Readonly<{
  messages: readonly ChatMessage[];
  onSend: (instruction: string) => void;
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
      <ol className="chat-log" aria-live="polite">
        {messages.length > 0 ? null : (
          <li className="chat-empty">Send an instruction to start.</li>
        )}
        {messages.map((message, index) => (
          <li
            key={index}
            className={`chat-message chat-message--${message.author}`}
          >
            <span className="chat-author">{message.author}</span>
            <p>{message.text}</p>
          </li>
        ))}
      </ol>
      <form
        className="chat-composer"
        onSubmit={(event) => {
          event.preventDefault();
          send();
        }}
      >
        <input
          aria-label="Instruction"
          maxLength={2000}
          placeholder="Send an instruction…"
          autoComplete="off"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
        />
        <button type="submit" disabled={draft.trim().length === 0}>
          Send
        </button>
      </form>
    </div>
  );
}
