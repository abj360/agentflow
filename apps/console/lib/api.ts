#!/usr/bin/env ts-node
/**
 * api.ts --- typed client for the agentflow API
 *
 * Contains:
 *   fetchTrace: loads the audit trace for one run
 *   fetchSessions: lists recent orchestration sessions
 *   TraceEventDto: wire shape of one audit event
 */

export interface TraceEventDto {
  event_hash: string;
  kind: string;
  payload: Record<string, unknown>;
}

export interface TraceResponse {
  trace_id: string;
  event_count: number;
  chain_valid: boolean;
  next_cursor: string | null;
  events: TraceEventDto[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Loads the audit trace for one run.
 *
 * @param traceId - Identifier of the run to fetch.
 * @returns trace - Parsed trace response from the API.
 */
export async function fetchTrace(traceId: string): Promise<TraceResponse> {
  const response = await fetch(`${API_BASE}/audit/${traceId}`);
  if (!response.ok) {
    throw new Error(`trace fetch failed: ${response.status}`);
  }
  return response.json();
}

/**
 * Lists recent orchestration sessions.
 *
 * @returns sessions - Recent session summaries from the API.
 */
export async function fetchSessions(): Promise<{ sessions: unknown[] }> {
  const response = await fetch(`${API_BASE}/audit/sessions`);
  if (!response.ok) {
    throw new Error(`sessions fetch failed: ${response.status}`);
  }
  return response.json();
}
