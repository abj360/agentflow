/**
 * api.ts --- typed client for the agentflow API
 *
 * Contains:
 *   ApprovalDecision: the two outcomes a reviewer can record
 *   Approval: one pending approval request as the API returns it
 *   fetchPendingApprovals: lists the approvals waiting on a reviewer
 *   Provider: which model the orchestrator reasons with, and whether it can
 *   readProvider: reports which provider is configured, without the key
 *   writeProvider: points the orchestrator at a provider and its credential
 *   writeModel: pins the team to one model the configured credential can reach
 *   RunSummary: what the API reports once a started run has finished
 *   startRun: hands one instruction to the orchestrator and streams the graph
 *   fetchTrace: loads the audit trace for one run
 *   resolveApproval: records a reviewer's decision on one approval request
 *   TraceEventDto: wire shape of one audit event
 */

export type ApprovalDecision = "approved" | "rejected";

export interface Approval {
  approval_id: string;
  trace_id: string;
  tool_name: string;
  status: string;
}

export interface Provider {
  configured: boolean;
  provider: string;
  model: string;
  providers: string[];
  models: string[];
}

export interface RunSummary {
  kind: string;
  status: string;
  tasks: number;
}

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

/**
 * Lists the approval requests currently waiting on a reviewer.
 *
 * @returns approvals - Pending approvals, empty when nothing is waiting.
 */
export async function fetchPendingApprovals(): Promise<Approval[]> {
  const response = await fetch(`${API_BASE}/approvals/pending`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`approvals fetch failed: ${response.status}`);
  }
  const body: { approvals?: Approval[] } = await response.json();
  return body.approvals ?? [];
}

/**
 * Hands one instruction to the orchestrator and streams the graph under a run.
 *
 * @param runId - Run the caller wants the task graph streamed under.
 * @param task - The instruction the coordinator should reason about.
 * @returns summary - What the turn did, and how the run it started ended.
 */
export async function startRun(
  runId: string,
  task: string,
): Promise<RunSummary> {
  const response = await fetch(
    `${API_BASE}/runs/${encodeURIComponent(runId)}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task }),
    },
  );
  if (!response.ok) {
    throw new Error(`run start failed: ${response.status}`);
  }
  return response.json();
}

/**
 * Reports which model the orchestrator reasons with, and whether it can.
 *
 * @returns provider - The configured model, never the credential itself.
 */
export async function readProvider(): Promise<Provider> {
  const response = await fetch(`${API_BASE}/settings/provider`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`provider read failed: ${response.status}`);
  }
  return response.json();
}

/**
 * Points the orchestrator at a provider and the credential to reason through.
 *
 * @param provider - Which provider the credential belongs to.
 * @param apiKey - Credential to hand the API, which never returns it.
 * @returns provider - The provider and model now in use.
 */
export async function writeProvider(
  provider: string,
  apiKey: string,
): Promise<Provider> {
  const response = await fetch(`${API_BASE}/settings/provider`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider, api_key: apiKey }),
  });
  if (!response.ok) {
    const body: { detail?: string } = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `provider write failed: ${response.status}`);
  }
  return response.json();
}

/**
 * Pins the team to one model the configured credential can reach.
 *
 * @param model - Model the reviewer wants every agent to reason through.
 * @returns provider - The provider and model now in use.
 */
export async function writeModel(model: string): Promise<Provider> {
  const response = await fetch(`${API_BASE}/settings/model`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model }),
  });
  if (!response.ok) {
    const body: { detail?: string } = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `model write failed: ${response.status}`);
  }
  return response.json();
}
