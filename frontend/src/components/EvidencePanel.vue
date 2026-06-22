<script setup lang="ts">
import type { EvidenceItem } from "../types/complaint";

const props = defineProps<{
  evidence: EvidenceItem[];
  degradedSources?: string[];
  retrievalMode?: string;
}>();
</script>

<template>
  <section class="panel" data-testid="evidence-panel">
    <p class="eyebrow">证据支持</p>
    <h2>证据面板</h2>
    <p
      v-if="
        (props.degradedSources?.length ?? 0) > 0 ||
        props.retrievalMode === 'elasticsearch-only' ||
        props.retrievalMode === 'milvus-only'
      "
      class="notice"
      data-testid="fallback-notice"
    >
      当前处于{{ props.retrievalMode === "milvus-only" ? " Milvus 单路检索" : " Elasticsearch 单路检索" }}降级模式
    </p>
    <ul v-if="props.evidence.length" class="evidence-list">
      <li v-for="item in props.evidence" :key="item.id">
        <strong>{{ item.title }}</strong>
        <p>
          来源：{{ item.sourceType }} · 条款：{{ item.articleNumber || "未标注" }} · 分值：{{
            item.score.toFixed(2)
          }}
        </p>
        <p>{{ item.contentSnapshot }}</p>
      </li>
    </ul>
    <p v-else class="empty">暂未检索到证据。</p>
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

.notice {
  margin: 0 0 14px;
  padding: 10px 12px;
  border-radius: 12px;
  background: #eef5fb;
  color: #315b83;
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
  background: #f8fbfe;
  border: 1px solid #e1ebf4;
}

.evidence-list p,
.evidence-list strong {
  color: #16324f;
}

.empty {
  color: #62809f;
}
</style>
