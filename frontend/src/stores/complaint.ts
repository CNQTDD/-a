import { defineStore } from "pinia";
import { computed, ref } from "vue";

import type {
  ComplaintSessionState,
  CreateSessionInput,
  SessionSnapshot,
  WorkflowEvent,
} from "../types/complaint";

function createInitialSession(input: CreateSessionInput): ComplaintSessionState {
  return {
    id: input.id,
    complaintText: input.complaintText,
    status: "draft",
    stage: "draft",
    intent: "",
    emotion: "",
    entities: [],
    riskLevel: null,
    degradedSources: [],
    evidence: [],
    streamedSolution: "",
    finalSolution: "",
    feedbackAction: null,
    feedbackReason: "",
    workflowError: "",
    lastSequence: 0,
    archived: false,
  };
}

export const useComplaintStore = defineStore("complaint", () => {
  const sessions = ref<Record<string, ComplaintSessionState>>({});
  const activeSessionId = ref<string | null>(null);
  const appliedEventIds = ref<string[]>([]);

  const activeSession = computed(() =>
    activeSessionId.value ? sessions.value[activeSessionId.value] ?? null : null,
  );

  function createSession(input: CreateSessionInput): ComplaintSessionState {
    const session = createInitialSession(input);
    sessions.value = {
      ...sessions.value,
      [input.id]: session,
    };
    activeSessionId.value = input.id;
    return session;
  }

  function restoreSession(snapshot: SessionSnapshot): ComplaintSessionState {
    const session: ComplaintSessionState = {
      id: snapshot.id,
      complaintText: snapshot.complaintText,
      status: snapshot.status,
      stage: snapshot.stage,
      intent: snapshot.intent ?? "",
      emotion: snapshot.emotion ?? "",
      entities: snapshot.entities ?? [],
      riskLevel: snapshot.riskLevel ?? null,
      degradedSources: [],
      evidence: snapshot.evidence ?? [],
      streamedSolution: snapshot.streamedSolution,
      finalSolution: snapshot.finalSolution ?? snapshot.streamedSolution,
      validation: snapshot.validation,
      feedbackAction: snapshot.feedbackAction ?? null,
      feedbackReason: snapshot.feedbackReason ?? "",
      workflowError: "",
      lastSequence: 0,
      archived: snapshot.archived ?? false,
    };
    sessions.value = {
      ...sessions.value,
      [snapshot.id]: session,
    };
    activeSessionId.value = snapshot.id;
    return session;
  }

  function applyEvent(event: WorkflowEvent): boolean {
    const session = sessions.value[event.sessionId];
    if (!session) {
      return false;
    }
    if (appliedEventIds.value.includes(event.id)) {
      return false;
    }
    if (event.sequence < session.lastSequence) {
      return false;
    }

    if (event.type === "workflow_started") {
      session.stage = event.stage;
      session.status = "running";
    } else if (event.type === "intent_completed") {
      session.intent = event.intent;
      session.emotion = event.emotion;
      session.entities = event.entities;
      session.stage = "intent";
      session.status = "running";
    } else if (event.type === "retrieval_completed") {
      session.evidence = event.evidence;
      session.degradedSources = event.degradedSources ?? [];
      session.stage = "retrieval";
      session.status = "running";
    } else if (event.type === "generation_delta") {
      session.streamedSolution += event.delta;
      session.status = "running";
      session.stage = "generation";
    } else if (event.type === "human_review_required") {
      session.riskLevel = event.riskLevel;
      session.stage = "manual";
      session.status = "awaiting_review";
    } else if (event.type === "validation_completed") {
      session.validation = event.validation;
      session.status = event.validation.status === "passed" ? "awaiting_review" : "failed";
      session.stage = "validation";
    } else if (event.type === "workflow_completed") {
      session.status = "resolved";
      session.stage = "resolved";
      session.finalSolution = session.streamedSolution;
    } else if (event.type === "workflow_failed") {
      session.status = "failed";
      session.stage = "failed";
      session.workflowError = event.reason;
    }

    session.lastSequence = event.sequence;
    appliedEventIds.value = [...appliedEventIds.value, event.id];
    return true;
  }

  function archiveSession(sessionId: string): void {
    const session = sessions.value[sessionId];
    if (!session) {
      return;
    }
    session.archived = true;
  }

  function recordFeedback(
    sessionId: string,
    feedbackAction: ComplaintSessionState["feedbackAction"],
    details: { reason?: string; solution?: string } = {},
  ): void {
    const session = sessions.value[sessionId];
    if (!session) {
      return;
    }
    session.feedbackAction = feedbackAction;
    session.feedbackReason = details.reason ?? "";
    if (details.solution) {
      session.finalSolution = details.solution;
    }
  }

  function resetSession(sessionId: string): void {
    const session = sessions.value[sessionId];
    if (!session) {
      return;
    }
    sessions.value[sessionId] = createInitialSession({
      id: session.id,
      complaintText: session.complaintText,
    });
  }

  return {
    sessions,
    activeSessionId,
    activeSession,
    appliedEventIds,
    createSession,
    applyEvent,
    restoreSession,
    archiveSession,
    recordFeedback,
    resetSession,
  };
});
