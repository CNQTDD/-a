<script setup lang="ts">
import type { ComplaintSessionState } from "../types/complaint";

defineProps<{
  session: ComplaintSessionState | null;
}>();
</script>

<template>
  <section class="panel">
    <p class="eyebrow">Solution Panel</p>
    <h2>Recommended response</h2>
    <template v-if="session">
      <p class="solution">{{ session.finalSolution || session.streamedSolution || "Waiting for stream..." }}</p>
      <p v-if="session.validation" class="validation">
        Validation: {{ session.validation.status }} - {{ session.validation.details }}
      </p>
    </template>
    <p v-else class="empty">No solution available yet.</p>
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

.solution {
  min-height: 72px;
  white-space: pre-wrap;
}

.empty,
.validation {
  color: rgba(244, 239, 231, 0.72);
}
</style>
