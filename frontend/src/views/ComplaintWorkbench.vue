<script setup lang="ts">
import { computed, ref } from "vue";

import {
  createComplaintSession,
  sendComplaintMessage,
  submitComplaintFeedback,
} from "../api/complaints";
import { streamEvents } from "../api/sse";
import ActionConfirmDialog from "../components/ActionConfirmDialog.vue";
import ActionNoticeBar from "../components/ActionNoticeBar.vue";
import ComplaintComposer from "../components/ComplaintComposer.vue";
import EvidencePanel from "../components/EvidencePanel.vue";
import FeedbackBar from "../components/FeedbackBar.vue";
import SessionSidebar from "../components/SessionSidebar.vue";
import SolutionPanel from "../components/SolutionPanel.vue";
import WorkflowTimeline from "../components/WorkflowTimeline.vue";
import { useComplaintStore } from "../stores/complaint";
import type { EvidenceItem, WorkflowEvent } from "../types/complaint";

const store = useComplaintStore();
const draftComplaint = ref("我的套餐费用和账单不一致，请帮我核实");
const draftEditedSolution = ref("");
const draftRejectReason = ref("");

const apiBaseUrl =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  resolveApiBaseUrl(window.location);

function resolveApiBaseUrl(location: Location | URL): string {
  if (location.port === "5280") {
    return `${location.protocol}//${location.hostname}:8000`;
  }
  if (location.port === "4173") {
    return `${location.protocol}//${location.hostname}:4174`;
  }
  return location.origin;
}

const activeSession = computed(() => store.activeSession);
const sessions = computed(() =>
  Object.values(store.sessions).filter((session) => !session.archived),
);
const pendingConfirmation = computed(() => store.pendingConfirmation);
const notice = computed(() => store.notice);
const hasSubmittingAction = computed(() =>
  Object.values(store.actionStatus).some((status) => status === "submitting"),
);

function normalizeComplaintText(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}

function createDraftIdempotencyKey(complaintText: string): string {
  const normalized = normalizeComplaintText(complaintText);
  let hash = 0;

  for (let index = 0; index < normalized.length; index += 1) {
    hash = (hash * 31 + normalized.charCodeAt(index)) >>> 0;
  }

  return `complaint-draft-${normalized.length}-${hash.toString(16)}`;
}

function createFeedbackIdempotencyKey(
  sessionId: string,
  action: string,
  payload: string,
): string {
  const normalized = `${sessionId}:${action}:${payload}`.trim();
  let hash = 0;

  for (let index = 0; index < normalized.length; index += 1) {
    hash = (hash * 31 + normalized.charCodeAt(index)) >>> 0;
  }

  return `feedback-${action}-${hash.toString(16)}`;
}

function normalizeEvidenceItem(item: Record<string, unknown>): EvidenceItem {
  return {
    id: String(item.id ?? item.evidence_id ?? "unknown-evidence"),
    sourceType: String(item.sourceType ?? item.source_type ?? "unknown"),
    title: String(item.title ?? item.source_id ?? "证据条目"),
    contentSnapshot: String(item.contentSnapshot ?? item.content_snapshot ?? ""),
    score: Number(item.score ?? 0),
    articleNumber: item.articleNumber
      ? String(item.articleNumber)
      : item.article
        ? String(item.article)
        : undefined,
  };
}

function normalizeWorkflowEvent(
  sessionId: string,
  sequence: number,
  rawEvent: { id: string; event: string; data: Record<string, unknown> | null },
): WorkflowEvent {
  const payload = rawEvent.data ?? {};

  switch (rawEvent.event) {
    case "workflow_started":
      return {
        id: rawEvent.id,
        sessionId,
        sequence,
        type: "workflow_started",
        stage: "intent",
      };
    case "intent_completed":
      return {
        id: rawEvent.id,
        sessionId,
        sequence,
        type: "intent_completed",
        intent: String(payload.intent ?? "unknown"),
        emotion: String(payload.emotion ?? "neutral"),
        entities: Array.isArray(payload.entities) ? payload.entities.map(String) : [],
      };
    case "retrieval_completed":
      return {
        id: rawEvent.id,
        sessionId,
        sequence,
        type: "retrieval_completed",
        evidence: Array.isArray(payload.evidence)
          ? payload.evidence.map((item) => normalizeEvidenceItem(item as Record<string, unknown>))
          : [],
        degradedSources: Array.isArray(payload.degradedSources)
          ? payload.degradedSources.map(String)
          : [],
        retrievalMode: payload.retrievalMode ? String(payload.retrievalMode) : undefined,
      };
    case "generation_delta":
      return {
        id: rawEvent.id,
        sessionId,
        sequence,
        type: "generation_delta",
        delta: String(payload.delta ?? payload.text ?? ""),
      };
    case "validation_completed": {
      const validation =
        payload.validation && typeof payload.validation === "object"
          ? (payload.validation as Record<string, unknown>)
          : payload;
      const status = String(validation.status ?? "warning");
      return {
        id: rawEvent.id,
        sessionId,
        sequence,
        type: "validation_completed",
        validation: {
          status:
            status === "passed" || status === "failed" || status === "warning"
              ? status
              : "warning",
          details: String(validation.details ?? ""),
        },
      };
    }
    case "human_review_required":
      return {
        id: rawEvent.id,
        sessionId,
        sequence,
        type: "human_review_required",
        riskLevel: "medium",
        reason: String(payload.reason ?? payload.route ?? "human_review"),
      };
    case "workflow_failed":
      return {
        id: rawEvent.id,
        sessionId,
        sequence,
        type: "workflow_failed",
        reason: String(payload.reason ?? "workflow failed"),
      };
    default:
      return {
        id: rawEvent.id,
        sessionId,
        sequence,
        type: "workflow_completed",
      };
  }
}

function requestStartWorkflow() {
  const complaintText = normalizeComplaintText(draftComplaint.value);
  if (!complaintText) {
    store.setNotice({
      tone: "error",
      message: "请先填写投诉内容，再启动处置流程。",
    });
    return;
  }

  store.requestConfirmation({
    kind: "start_workflow",
    title: "确认启动处置流程",
    message: "系统将为当前投诉创建或复用会话，并启动一次完整的处置流程。",
    confirmLabel: "确认启动",
  });
}

function requestAccept() {
  if (!activeSession.value) {
    return;
  }

  store.requestConfirmation({
    kind: "accept_feedback",
    title: "确认采纳方案",
    message: "采纳后将把当前方案作为人工确认结果保留下来。",
    confirmLabel: "确认采纳",
  });
}

function requestEdit(solution: string) {
  if (!activeSession.value) {
    return;
  }

  draftEditedSolution.value = solution;
  store.requestConfirmation({
    kind: "edit_feedback",
    title: "确认编辑后采纳",
    message: "系统将把修订后的内容作为最终处置方案保存。",
    confirmLabel: "确认提交",
  });
}

function requestReject(reason: string) {
  if (!activeSession.value) {
    return;
  }

  draftRejectReason.value = reason;
  store.requestConfirmation({
    kind: "reject_feedback",
    title: "确认驳回处理",
    message: "驳回后当前会话会进入失败状态，并保留驳回原因。",
    confirmLabel: "确认驳回",
  });
}

function requestArchive() {
  if (!activeSession.value) {
    return;
  }

  store.requestConfirmation({
    kind: "archive_session",
    title: "确认归档会话",
    message: "归档后会话将从活跃工作区隐藏，但仍保留历史记录。",
    confirmLabel: "确认归档",
  });
}

async function confirmAction() {
  const confirmation = pendingConfirmation.value;
  if (!confirmation) {
    return;
  }

  store.clearNotice();

  if (confirmation.kind === "start_workflow") {
    store.clearPendingConfirmation();
    await startSessionWithRetry();
    return;
  }

  if (!activeSession.value) {
    store.clearPendingConfirmation();
    return;
  }

  if (confirmation.kind === "accept_feedback") {
    store.clearPendingConfirmation();
    await submitFeedbackAction("accepted");
    return;
  }

  if (confirmation.kind === "edit_feedback") {
    store.clearPendingConfirmation();
    await submitFeedbackAction("edited", draftEditedSolution.value);
    draftEditedSolution.value = "";
    return;
  }

  if (confirmation.kind === "reject_feedback") {
    store.clearPendingConfirmation();
    await submitFeedbackAction("rejected", undefined, draftRejectReason.value);
    draftRejectReason.value = "";
    return;
  }

  if (confirmation.kind === "archive_session") {
    store.clearPendingConfirmation();
    store.markActionStatus("archive_session", "submitting");
    store.archiveSession(activeSession.value.id);
    store.markActionStatus("archive_session", "idle");
    store.setNotice({
      tone: "success",
      message: "会话已归档，不再显示在活跃工作区。",
    });
  }
}

function cancelConfirmation() {
  draftEditedSolution.value = "";
  draftRejectReason.value = "";
  store.clearPendingConfirmation();
}

async function startSessionWithRetry() {
  store.markActionStatus("start_workflow", "submitting");
  const complaintText = normalizeComplaintText(draftComplaint.value);

  const reusableSessionId = store.findReusableSessionId(complaintText);
  if (reusableSessionId) {
    store.activeSessionId = reusableSessionId;
    store.markActionStatus("start_workflow", "idle");
    store.setNotice({
      tone: "info",
      message: "已切回相同投诉内容的未归档会话，无需重复新建。",
    });
    return;
  }

  const idempotencyKey = createDraftIdempotencyKey(complaintText);

  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      const created = await createComplaintSession(
        apiBaseUrl,
        {
          id: `session-${Date.now()}`,
          complaintText,
        },
        {
          idempotencyKey,
        },
      );
      const sessionId = created.session_id ?? created.id;
      if (!sessionId) {
        throw new Error("会话创建响应缺少会话 ID。");
      }

      const session = store.createSession({
        id: sessionId,
        complaintText,
      });

      await sendComplaintMessage(apiBaseUrl, session.id, complaintText);

      let sequence = 0;
      for await (const event of streamEvents<Record<string, unknown>>(
        `${apiBaseUrl}/api/v1/complaints/${session.id}/events`,
      )) {
        sequence += 1;
        const normalizedEvent = normalizeWorkflowEvent(session.id, sequence, {
          id: event.id,
          event: event.event,
          data: event.data,
        });
        store.applyEvent(
          normalizedEvent,
        );

        if (normalizedEvent.type === "human_review_required") {
          store.setNotice({
            tone: "info",
            message: `流程已进入人工复核，请结合证据与风险信息继续处理。原因：${normalizedEvent.reason}`,
          });
        }

        if (normalizedEvent.type === "workflow_failed") {
          store.setNotice({
            tone: "error",
            message: `流程转入人工兜底，请检查检索服务状态或改为人工处理。原因：${normalizedEvent.reason}`,
          });
        }
      }

      store.markActionStatus("start_workflow", "idle");
      return;
    } catch (error) {
      if (attempt === 0) {
        store.setNotice({
          tone: "info",
          message: "启动失败，系统已自动重试一次。",
        });
        continue;
      }

      store.markActionStatus("start_workflow", "retryable");
      store.setNotice({
        tone: "error",
        message: error instanceof Error ? error.message : "启动处置流程失败，请稍后重试。",
      });
      return;
    }
  }
}

async function submitFeedbackAction(
  action: "accepted" | "edited" | "rejected",
  editedSolution?: string,
  rejectReason?: string,
) {
  const session = activeSession.value;
  if (!session) {
    return;
  }

  const kind =
    action === "accepted"
      ? "accept_feedback"
      : action === "edited"
        ? "edit_feedback"
        : "reject_feedback";

  store.markActionStatus(kind, "submitting");

  try {
    await submitComplaintFeedback(
      apiBaseUrl,
      session.id,
      {
        action,
        edited_solution: editedSolution,
        reject_reason: rejectReason,
      },
      {
        idempotencyKey: createFeedbackIdempotencyKey(
          session.id,
          action,
          `${editedSolution ?? ""}:${rejectReason ?? ""}`,
        ),
      },
    );

    if (action === "accepted") {
      store.recordFeedback(session.id, "accept");
      store.setNotice({
        tone: "success",
        message: "方案已采纳，已同步记录到会话反馈。",
      });
    } else if (action === "edited") {
      store.recordFeedback(session.id, "edited", {
        solution: editedSolution,
      });
      store.setNotice({
        tone: "success",
        message: "修订方案已提交并采纳。",
      });
    } else {
      store.recordFeedback(session.id, "rejected", {
        reason: rejectReason,
      });
      store.setNotice({
        tone: "success",
        message: "驳回原因已提交，会话已转入失败状态。",
      });
    }

    store.markActionStatus(kind, "idle");
  } catch (error) {
    store.markActionStatus(kind, "retryable");
    store.setNotice({
      tone: "error",
      message: error instanceof Error ? error.message : "反馈提交失败，请再次确认后重试。",
    });
  }
}

function selectSession(sessionId: string) {
  store.activeSessionId = sessionId;
}
</script>

<template>
  <main class="workbench">
    <SessionSidebar
      :sessions="sessions"
      :active-session-id="store.activeSessionId"
      @select="selectSession"
    />

    <section class="center-pane">
      <header class="hero">
        <p class="eyebrow">诉智达工作台</p>
        <h1>投诉处置工作台</h1>
        <p class="subtitle">
          面向客服与运营坐席的投诉处置工作台，支持流程追踪、证据查看、方案生成与人工反馈闭环。
        </p>
      </header>

      <ActionNoticeBar :notice="notice" @dismiss="store.clearNotice()" />

      <ComplaintComposer
        v-model="draftComplaint"
        :busy="store.actionStatus.start_workflow === 'submitting'"
        @submit="requestStartWorkflow"
      />

      <WorkflowTimeline :session="activeSession" />
      <SolutionPanel :session="activeSession" />
      <FeedbackBar
        :session="activeSession"
        :pending="hasSubmittingAction"
        @accept="requestAccept"
        @edit="requestEdit"
        @reject="requestReject"
        @archive="requestArchive"
      />
    </section>

    <aside class="right-pane">
      <EvidencePanel
        :evidence="activeSession?.evidence ?? []"
        :degraded-sources="activeSession?.degradedSources ?? []"
        :retrieval-mode="activeSession?.retrievalMode"
      />
      <section class="panel notice-panel">
        <p class="eyebrow">辅助提示</p>
        <h2>处置上下文</h2>
        <p class="muted">
          这里集中展示证据状态、风险信息、校验结果和人工反馈，帮助坐席快速完成处置判断。
        </p>
      </section>
    </aside>

    <ActionConfirmDialog
      :open="pendingConfirmation !== null"
      :title="pendingConfirmation?.title ?? ''"
      :message="pendingConfirmation?.message ?? ''"
      :confirm-label="pendingConfirmation?.confirmLabel ?? '确认'"
      :busy="hasSubmittingAction"
      @cancel="cancelConfirmation"
      @confirm="confirmAction"
    />
  </main>
</template>

<style scoped>
.workbench {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr) 320px;
  gap: 20px;
  padding: 24px;
  background:
    radial-gradient(circle at top left, rgba(180, 208, 234, 0.45), transparent 26%),
    radial-gradient(circle at bottom right, rgba(229, 238, 247, 0.9), transparent 32%),
    linear-gradient(180deg, #f8fbff 0%, #eef4f9 46%, #f7f3ea 100%);
  color: #16324f;
  font-family: "Microsoft YaHei UI", "PingFang SC", "Noto Sans SC", sans-serif;
}

.center-pane,
.right-pane {
  display: grid;
  gap: 20px;
  align-content: start;
}

.hero,
.panel {
  padding: 22px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(145, 173, 201, 0.28);
  box-shadow: 0 18px 42px rgba(34, 74, 118, 0.08);
}

.eyebrow {
  margin: 0 0 8px;
  letter-spacing: 0.14em;
  font-size: 0.72rem;
  color: #4f7aa3;
}

.subtitle,
.muted {
  color: #57718d;
}

h1,
h2 {
  margin: 0;
  color: #123252;
}

h1 {
  margin-bottom: 10px;
  font-size: 2.1rem;
  line-height: 1.2;
}

.notice-panel {
  min-height: 180px;
}

@media (max-width: 1100px) {
  .workbench {
    grid-template-columns: 1fr;
  }
}
</style>
