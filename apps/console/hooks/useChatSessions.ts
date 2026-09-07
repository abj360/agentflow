/**
 * useChatSessions.ts --- the sessions a reviewer has opened, newest first
 *
 * Contains:
 *   STORAGE_KEY: where the session list is remembered for this browser
 *   ChatSession: one session, and the run its task graph belongs to
 *   newRunId(): mints the id a fresh session's run is streamed under
 *   useChatSessions(): lists remembered sessions, records and forgets them
 */

"use client";

import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "agentflow.sessions";

export interface ChatSession {
  id: string;
  title: string;
  openedAt: number;
}

/**
 * Mints the id a fresh session's run is streamed under.
 *
 * @returns runId - An id unique enough to key one run's graph on.
 */
export function newRunId(): string {
  return `run-${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
}

/**
 * Lists the sessions this browser has opened and records new ones.
 *
 * Sessions live in this browser rather than on the server: a run's own history is
 * already in the audit log, and this list is only how one reviewer gets back to
 * the runs they were looking at.
 *
 * @returns sessions - The remembered sessions, and the callbacks that record
 *   and forget one.
 */
export function useChatSessions() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored !== null) {
        setSessions(JSON.parse(stored) as ChatSession[]);
      }
    } catch {
      // a browser with storage blocked still gets a usable, unremembered list
    }
  }, []);

  const remember = useCallback((id: string, title: string) => {
    setSessions((previous) => {
      const withoutThisRun = previous.filter((session) => session.id !== id);
      const next = [{ id, title, openedAt: Date.now() }, ...withoutThisRun];
      try {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      } catch {
        // losing the list is not worth failing the run the reviewer just started
      }
      return next;
    });
  }, []);

  const forget = useCallback((id: string) => {
    setSessions((previous) => {
      const next = previous.filter((session) => session.id !== id);
      try {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      } catch {
        // the row is gone from this list either way; remembering that is a bonus
      }
      return next;
    });
  }, []);

  return { sessions, remember, forget };
}
