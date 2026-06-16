<script setup lang="ts">
import type { EvidenceItem } from "../types/complaint";

defineProps<{
  evidence: EvidenceItem[];
}>();
</script>

<template>
  <section class="panel" data-testid="evidence-panel">
    <p class="eyebrow">Evidence Panel</p>
    <h2>Retrieved evidence</h2>
    <p
      v-if="evidence.some((item) => item.sourceType === 'business_rule')"
      class="notice"
      data-testid="fallback-notice"
    >
      Elasticsearch-only fallback active
    </p>
    <ul v-if="evidence.length" class="evidence-list">
      <li v-for="item in evidence" :key="item.id">
        <strong>{{ item.title }}</strong>
        <p>{{ item.sourceType }} · {{ item.articleNumber || "n/a" }} · {{ item.score.toFixed(2) }}</p>
        <p>{{ item.contentSnapshot }}</p>
      </li>
    </ul>
    <p v-else class="empty">No evidence retrieved yet.</p>
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

.evidence-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 12px;
}

.evidence-list li {
  padding: 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
}

.empty {
  color: rgba(244, 239, 231, 0.72);
}
</style>
