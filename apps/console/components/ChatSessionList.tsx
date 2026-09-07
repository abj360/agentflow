/**
 * ChatSessionList.tsx --- the sessions a reviewer can move between, in the left sidebar
 *
 * Contains:
 *   ChatSessionList: lists remembered sessions and starts a new one
 */

"use client";

import type { ChatSession } from "../hooks/useChatSessions";

/**
 * Lists the sessions this browser remembers and starts a new one.
 *
 * @param props.sessions - Chat sessions opened in this browser, newest first.
 * @param props.currentId - Run the reviewer is looking at now.
 * @param props.onOpen - Called with the run a reviewer wants to switch to.
 * @param props.onNew - Called when a reviewer wants a fresh session.
 * @param props.onHide - Called when a reviewer wants the sidebar out of the way.
 * @returns The session list element.
 */
export function ChatSessionList({
  sessions,
  currentId,
  onOpen,
  onNew,
  onHide,
}: Readonly<{
  sessions: readonly ChatSession[];
  currentId: string;
  onOpen: (runId: string) => void;
  onNew: () => void;
  onHide: () => void;
}>) {
  return (
    <nav className="sessions">
      <div className="sessions__head">
        <p className="sessions__title">Chats</p>
        <span className="sessions__actions">
          <button className="sessions__new" onClick={onNew} title="New chat">
            +
          </button>
          <button
            className="sessions__hide"
            onClick={onHide}
            aria-label="Hide the sidebar"
            title="Hide the sidebar"
          >
            ‹
          </button>
        </span>
      </div>
      {sessions.length === 0 ? (
        <p className="sessions__empty">No chats yet</p>
      ) : (
        <ul className="sessions__list">
          {sessions.map((session) => (
            <li key={session.id}>
              <button
                className={
                  session.id === currentId
                    ? "sessions__row sessions__row--selected"
                    : "sessions__row"
                }
                aria-current={session.id === currentId}
                onClick={() => onOpen(session.id)}
              >
                {session.title}
              </button>
            </li>
          ))}
        </ul>
      )}
    </nav>
  );
}
