<script setup lang="ts">
import type { ComplaintSessionState } from "../types/complaint";
import { formatValidationLabel } from "../presentation/complaint-display";

defineProps<{
  session: ComplaintSessionState | null;
}>();
</script>

<template>
  <section class="panel">
    <p class="eyebrow">方案输出</p>
    <h2>处置建议</h2>
    <template v-if="session">
      <p class="solution">
        {{ session.finalSolution || session.streamedSolution || "正在等待流程输出处置建议..." }}
      </p>
      <p v-if="session.validation" class="validation">
        校验结果：{{ formatValidationLabel(session.validation.status) }} - {{ session.validation.details }}
      </p>
    </template>
    <p v-else class="empty">当前还没有生成处置建议。</p>
  </section>
</template>

<style scoped>
.panel {
  padding: 20px;
  border-radius: 18px;
  background: #ffffff;
  border: 1px solid #d8e4ef;
  box-shadow: 0 12px 30px rgba(31, 79, 126, 0.08);
}

.eyebrow {
  margin: 0 0 8px;
  letter-spacing: 0.14em;
  font-size: 0.72rem;
  color: #4f7aa3;
}

h2 {
  color: #123252;
}

.solution {
  min-height: 72px;
  white-space: pre-wrap;
  color: #16324f;
  line-height: 1.75;
}

.empty,
.validation {
  color: #62809f;
}
</style>
