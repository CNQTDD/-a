export type ComplaintStage =
  | "draft"
  | "intent"
  | "retrieval"
  | "generation"
  | "validation"
  | "manual"
  | "resolved"
  | "failed";

export type ValidationStatus = "passed" | "failed" | "warning";

export type RiskLevel = "low" | "medium" | "high";

export type FeedbackAction = "accept" | "edited" | "rejected";

export interface EvidenceItem {
  id: string;
  sourceType: string;
  title: string;
  contentSnapshot: string;
  score: number;
  articleNumber?: string;
}

export interface ValidationResult {
  status: ValidationStatus;
  details: string;
}

export interface ComplaintSessionState {
  id: string;
  complaintText: string;
  status: "draft" | "running" | "awaiting_review" | "resolved" | "failed";
  stage: ComplaintStage;
  intent: string;
  emotion: string;
  entities: string[];
  riskLevel: RiskLevel | null;
  degradedSources: string[];
  evidence: EvidenceItem[];
  streamedSolution: string;
  finalSolution: string;
  validation?: ValidationResult;
  feedbackAction: FeedbackAction | null;
  feedbackReason: string;
  workflowError: string;
  lastSequence: number;
  archived: boolean;
}

export interface WorkflowEventBase {
  id: string;
  sessionId: string;
  sequence: number;
}

export interface WorkflowStartedEvent extends WorkflowEventBase {
  type: "workflow_started";
  stage: Exclude<ComplaintStage, "draft">;
}

export interface GenerationDeltaEvent extends WorkflowEventBase {
  type: "generation_delta";
  delta: string;
}

export interface IntentCompletedEvent extends WorkflowEventBase {
  type: "intent_completed";
  intent: string;
  emotion: string;
  entities: string[];
}

export interface RetrievalCompletedEvent extends WorkflowEventBase {
  type: "retrieval_completed";
  evidence: EvidenceItem[];
  degradedSources?: string[];
  retrievalMode?: string;
}

export interface ValidationCompletedEvent extends WorkflowEventBase {
  type: "validation_completed";
  validation: ValidationResult;
}

export interface HumanReviewRequiredEvent extends WorkflowEventBase {
  type: "human_review_required";
  riskLevel: RiskLevel;
  reason: string;
}

export interface WorkflowCompletedEvent extends WorkflowEventBase {
  type: "workflow_completed";
}

export interface WorkflowFailedEvent extends WorkflowEventBase {
  type: "workflow_failed";
  reason: string;
}

export type WorkflowEvent =
  | WorkflowStartedEvent
  | IntentCompletedEvent
  | RetrievalCompletedEvent
  | GenerationDeltaEvent
  | HumanReviewRequiredEvent
  | ValidationCompletedEvent
  | WorkflowCompletedEvent
  | WorkflowFailedEvent;

export interface CreateSessionInput {
  id: string;
  complaintText: string;
}

export interface SessionSnapshot {
  id: string;
  complaintText: string;
  status: ComplaintSessionState["status"];
  stage: ComplaintStage;
  intent?: string;
  emotion?: string;
  entities?: string[];
  riskLevel?: RiskLevel | null;
  evidence?: EvidenceItem[];
  streamedSolution: string;
  finalSolution?: string;
  validation?: ValidationResult;
  feedbackAction?: FeedbackAction | null;
  feedbackReason?: string;
  archived?: boolean;
}
