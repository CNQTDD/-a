import { getJson, postJson } from "./client";
import type {
  CreateSessionInput,
  SessionSnapshot,
  WorkflowEvent,
} from "../types/complaint";

const DEFAULT_DEMO_USER_ID = "11111111-1111-4111-8111-111111111111";

export interface CreateSessionResponse {
  id?: string;
  session_id?: string;
}

export interface CreateSessionOptions {
  idempotencyKey?: string;
}

export interface FeedbackOptions {
  idempotencyKey?: string;
}

export interface SendComplaintResponse {
  run_id: string;
}

export function createComplaintSession(
  baseUrl: string,
  input: CreateSessionInput,
  options: CreateSessionOptions = {},
) {
  return postJson<CreateSessionResponse>(
    `${baseUrl}/api/v1/complaints/sessions`,
    {
      id: input.id,
      user_id: DEFAULT_DEMO_USER_ID,
      complaint_text: input.complaintText,
    },
    undefined,
    options.idempotencyKey
      ? {
          "Idempotency-Key": options.idempotencyKey,
        }
      : undefined,
  );
}

export function sendComplaintMessage(
  baseUrl: string,
  sessionId: string,
  complaintText: string,
) {
  return postJson<SendComplaintResponse>(
    `${baseUrl}/api/v1/complaints/${sessionId}/messages`,
    {
      message: complaintText,
      complaint_text: complaintText,
    },
  );
}

export function loadComplaintSession(baseUrl: string, sessionId: string) {
  return getJson<SessionSnapshot>(`${baseUrl}/api/v1/complaints/${sessionId}`);
}

export function submitComplaintFeedback(
  baseUrl: string,
  sessionId: string,
  payload: Record<string, unknown>,
  options: FeedbackOptions = {},
) {
  return postJson<Record<string, unknown>>(
    `${baseUrl}/api/v1/complaints/${sessionId}/feedback`,
    payload,
    undefined,
    options.idempotencyKey
      ? {
          "Idempotency-Key": options.idempotencyKey,
        }
      : undefined,
  );
}

export type { WorkflowEvent };
