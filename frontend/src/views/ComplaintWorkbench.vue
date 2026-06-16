<script setup lang="ts">
import { computed, ref } from "vue";

import ComplaintComposer from "../components/ComplaintComposer.vue";
import EvidencePanel from "../components/EvidencePanel.vue";
import FeedbackBar from "../components/FeedbackBar.vue";
import SessionSidebar from "../components/SessionSidebar.vue";
import SolutionPanel from "../components/SolutionPanel.vue";
import WorkflowTimeline from "../components/WorkflowTimeline.vue";
import { createComplaintSession, sendComplaintMessage } from "../api/complaints";
import { streamEvents } from "../api/sse";
import { useComplaintStore } from "../stores/complaint";
import type { WorkflowEvent } from "../types/complaint";

const store = useComplaintStore();
const draftComplaint = ref("我的套餐费用和账单不一致");
const busy = ref(false);
const apiBaseUrl =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  (window.location.port === "4173" ? "http://127.0.0.1:4174" : window.location.origin);

const activeSession = computed(() => store.activeSession);
const sessions = computed(() => Object.values(store.sessions));

async function startSession() {
  busy.value = true;
  try {
    const complaintText = draftComplaint.value.trim() || "未填写投诉内容";
    const created = await createComplaintSession(apiBaseUrl, {
      id: `session-${Date.now()}`,
      complaintText,
    });
    const session = store.createSession({
      id: created.session_id,
      complaintText,
    });

    await sendComplaintMessage(apiBaseUrl, session.id, complaintText);

    for await (const event of streamEvents<WorkflowEvent>(
      `${apiBaseUrl}/api/v1/complaints/${session.id}/events`,
    )) {
      store.applyEvent(event.data);
    }
  } finally {
    busy.value = false;
  }
}

function selectSession(sessionId: string) {
  store.activeSessionId = sessionId;
}

function handleAccept() {
  if (!activeSession.value) {
    return;
  }
  store.recordFeedback(activeSession.value.id, "accept");
  store.archiveSession(activeSession.value.id);
}

function handleEdit(solution: string) {
  if (!activeSession.value) {
    return;
  }
  store.recordFeedback(activeSession.value.id, "edited", { solution });
}

function handleReject(reason: string) {
  if (!activeSession.value) {
    return;
  }
  store.recordFeedback(activeSession.value.id, "rejected", { reason });
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
        <p class="eyebrow">Case intake</p>
        <h1>Process complaints with a guided, traceable flow.</h1>
        <p class="subtitle">
          The workbench keeps state in Pinia, streams workflow updates, and
          highlights the current decision point for the operator.
        </p>
      </header>

      <ComplaintComposer
        v-model="draftComplaint"
        :busy="busy"
        @submit="startSession"
      />

      <WorkflowTimeline :session="activeSession" />
      <SolutionPanel :session="activeSession" />
      <FeedbackBar
        :session="activeSession"
        @accept="handleAccept"
        @edit="handleEdit"
        @reject="handleReject"
      />
    </section>

    <aside class="right-pane">
      <EvidencePanel :evidence="activeSession?.evidence ?? []" />
      <section class="panel notice">
        <p class="eyebrow">Evidence Status</p>
        <h2>Operator context</h2>
        <p class="muted">
          Retrieved evidence and feedback state appear here alongside risk and
          validation data.
        </p>
      </section>
    </aside>
  </main>
</template>

<style scoped>
.workbench {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr) 320px;
  gap: 20px;
  padding: 20px;
  background:
    radial-gradient(circle at top left, rgba(214, 186, 146, 0.18), transparent 30%),
    linear-gradient(135deg, #1c1d21 0%, #23252b 40%, #111316 100%);
  color: #f4efe7;
}

.center-pane,
.right-pane {
  display: grid;
  gap: 20px;
  align-content: start;
}

.hero,
.panel {
  padding: 20px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.eyebrow {
  margin: 0 0 8px;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  font-size: 0.72rem;
  color: #c9a66b;
}

.subtitle,
.muted {
  color: rgba(244, 239, 231, 0.72);
}

h1,
h2 {
  margin: 0;
}

.notice {
  min-height: 180px;
}

@media (max-width: 1100px) {
  .workbench {
    grid-template-columns: 1fr;
  }
}
</style>
