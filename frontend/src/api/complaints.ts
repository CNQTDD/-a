import { getJson, postJson } from "./client";
import type {
  CreateSessionInput,
  SessionSnapshot,
  WorkflowEvent,
} from "../types/complaint";

export interface CreateSessionResponse {
  session_id: string;
}

export interface SendComplaintResponse {
  run_id: string;
}

export function createComplaintSession(baseUrl: string, input: CreateSessionInput) {
  return postJson<CreateSessionResponse>(`${baseUrl}/api/v1/complaints/sessions`, input);
}

export function sendComplaintMessage(
  baseUrl: string,
  sessionId: string,
  complaintText: string,
) {
  return postJson<SendComplaintResponse>(
    `${baseUrl}/api/v1/complaints/${sessionId}/messages`,
    { complaint_text: complaintText },
  );
}

export function loadComplaintSession(baseUrl: string, sessionId: string) {
  return getJson<SessionSnapshot>(`${baseUrl}/api/v1/complaints/${sessionId}`);
}

export function submitComplaintFeedback(
  baseUrl: string,
  sessionId: string,
  payload: Record<string, unknown>,
) {
  return postJson<Record<string, unknown>>(
    `${baseUrl}/api/v1/complaints/${sessionId}/feedback`,
    payload,
  );
}

export type { WorkflowEvent };
