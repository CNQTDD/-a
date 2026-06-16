<script setup lang="ts">
import type { ComplaintSessionState } from "../types/complaint";

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
    <p class="eyebrow">Session Sidebar</p>
    <h2>Sessions</h2>
    <ul class="list">
      <li
        v-for="session in sessions"
        :key="session.id"
        :class="{ active: session.id === activeSessionId }"
      >
        <button type="button" @click="emit('select', session.id)">
          <strong>{{ session.id }}</strong>
          <span>{{ session.stage }}</span>
        </button>
      </li>
    </ul>
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

.list {
  list-style: none;
  padding: 0;
  margin: 16px 0 0;
  display: grid;
  gap: 10px;
}

button {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.05);
  color: inherit;
  text-align: left;
}

li.active button {
  background: rgba(201, 166, 107, 0.16);
  border-color: rgba(201, 166, 107, 0.45);
}

span {
  display: block;
  margin-top: 4px;
  color: rgba(244, 239, 231, 0.72);
}
</style>
