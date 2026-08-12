/**
 * api.ts --- typed client for the agentflow API
 *
 * Contains:
 *   ApprovalDecision: the two outcomes a reviewer can record
 *   fetchTrace: loads the audit trace for one run
 *   fetchSessions: lists recent orchestration sessions
 *   resolveApproval: records a reviewer's decision on one approval request
 *   TraceEventDto: wire shape of one audit event
 */

export type ApprovalDecision = "approved" | "rejected";

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
  const response = await fetch(`${API_BASE}/audit/${traceId}`, {
    cache: "no-store",
  });
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

/**
 * Records a reviewer's decision on one approval request.
 *
 * @param approvalId - Identifier of the approval being decided.
 * @param status - The decision to record against the approval.
 * @returns accepted - True when the API recorded the decision.
 */
export async function resolveApproval(
  approvalId: string,
  status: ApprovalDecision,
): Promise<boolean> {
  const response = await fetch(`${API_BASE}/approvals/${approvalId}/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  return response.ok;
}
