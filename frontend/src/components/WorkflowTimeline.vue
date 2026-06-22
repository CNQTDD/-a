<script setup lang="ts">
import type { ComplaintSessionState } from "../types/complaint";
import {
  formatEmotionLabel,
  formatFeedbackActionLabel,
  formatIntentLabel,
  formatRiskLevelLabel,
  formatSourceLabel,
  formatStageLabel,
  formatStatusLabel,
  formatValidationLabel,
} from "../presentation/complaint-display";

defineProps<{
  session: ComplaintSessionState | null;
}>();
</script>

<template>
  <section class="panel" data-testid="workflow-timeline">
    <p class="eyebrow">流程跟踪</p>
    <h2>流程进度</h2>
    <div v-if="session" class="timeline">
      <p><strong>状态：</strong> {{ formatStatusLabel(session.status) }}</p>
      <p><strong>阶段：</strong> {{ formatStageLabel(session.stage) }}</p>
      <p><strong>意图：</strong> {{ session.intent ? formatIntentLabel(session.intent) : "待识别" }}</p>
      <p><strong>情绪：</strong> {{ session.emotion ? formatEmotionLabel(session.emotion) : "待识别" }}</p>
      <p><strong>实体：</strong> {{ session.entities.join("、") || "待识别" }}</p>
      <p v-if="session.riskLevel">
        <strong>风险等级：</strong> {{ formatRiskLevelLabel(session.riskLevel) }}
      </p>
      <p v-if="session.degradedSources.length">
        <strong>降级来源：</strong>
        {{ session.degradedSources.map((source) => formatSourceLabel(source)).join("、") }}
      </p>
      <p v-if="session.validation">
        <strong>校验结果：</strong>
        {{ formatValidationLabel(session.validation.status) }} - {{ session.validation.details }}
      </p>
      <p v-if="session.workflowError"><strong>流程异常：</strong> {{ session.workflowError }}</p>
      <p v-if="session.feedbackAction">
        <strong>反馈动作：</strong> {{ formatFeedbackActionLabel(session.feedbackAction) }}
      </p>
      <p v-if="session.status === 'resolved'">流程已完成</p>
      <p v-if="session.status === 'failed'">需要人工兜底处理</p>
    </div>
    <p v-else class="empty">当前还没有激活的投诉会话。</p>
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

.timeline {
  display: grid;
  gap: 10px;
}

.timeline p {
  margin: 0;
  color: #244869;
}

.empty {
  color: #62809f;
}
</style>
