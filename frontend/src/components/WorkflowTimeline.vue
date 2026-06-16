<script setup lang="ts">
import type { ComplaintSessionState } from "../types/complaint";

defineProps<{
  session: ComplaintSessionState | null;
}>();
</script>

<template>
  <section class="panel" data-testid="workflow-timeline">
    <p class="eyebrow">Workflow Timeline</p>
    <h2>State progression</h2>
    <div v-if="session" class="timeline">
      <p><strong>Status:</strong> {{ session.status }}</p>
      <p><strong>Stage:</strong> {{ session.stage }}</p>
      <p><strong>Intent:</strong> {{ session.intent || "Pending" }}</p>
      <p><strong>Emotion:</strong> {{ session.emotion || "Pending" }}</p>
      <p><strong>Entities:</strong> {{ session.entities.join(", ") || "Pending" }}</p>
      <p v-if="session.riskLevel"><strong>Risk:</strong> {{ session.riskLevel }}</p>
      <p v-if="session.degradedSources.length">
        <strong>Degraded:</strong> {{ session.degradedSources.join(", ") }}
      </p>
      <p v-if="session.validation">
        <strong>Validation:</strong> {{ session.validation.status }} -
        {{ session.validation.details }}
      </p>
      <p v-if="session.workflowError"><strong>Workflow error:</strong> {{ session.workflowError }}</p>
      <p v-if="session.feedbackAction">
        <strong>Feedback:</strong> {{ session.feedbackAction }}
      </p>
      <p v-if="session.status === 'resolved' || session.status === 'completed'">Workflow finalized</p>
      <p v-if="session.status === 'failed'">Manual handling required</p>
    </div>
    <p v-else class="empty">No active session yet.</p>
  </section>
</template>

<style scoped>
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

.empty {
  color: rgba(244, 239, 231, 0.72);
}
</style>
