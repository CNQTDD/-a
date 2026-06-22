<script setup lang="ts">
import type { ComplaintSessionState } from "../types/complaint";
import { formatStageLabel } from "../presentation/complaint-display";

defineProps<{
  sessions: ComplaintSessionState[];
  activeSessionId: string | null;
}>();

const emit = defineEmits<{
  select: [sessionId: string];
}>();
</script>

<template>
  <section class="panel">
    <p class="eyebrow">会话列表</p>
    <h2>投诉会话</h2>
    <ul class="list">
      <li
        v-for="session in sessions"
        :key="session.id"
        :class="{ active: session.id === activeSessionId }"
      >
        <button type="button" @click="emit('select', session.id)">
          <strong>{{ session.id }}</strong>
          <span>{{ formatStageLabel(session.stage) }}</span>
        </button>
      </li>
    </ul>
    <p v-if="sessions.length === 0" class="empty">当前还没有投诉会话。</p>
  </section>
</template>

<style scoped>
.panel {
  padding: 20px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.9);
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

.list {
  list-style: none;
  padding: 0;
  margin: 16px 0 0;
  display: grid;
  gap: 10px;
}

button {
  width: 100%;
  border: 1px solid #d8e4ef;
  border-radius: 14px;
  padding: 12px 14px;
  background: #f8fbfe;
  color: #16324f;
  text-align: left;
}

li.active button {
  background: #e8f1f9;
  border-color: #6c98bf;
}

span {
  display: block;
  margin-top: 4px;
  color: #62809f;
}

.empty {
  margin: 16px 0 0;
  color: #62809f;
}
</style>
