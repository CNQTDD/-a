<script setup lang="ts">
import type { ActionNotice } from "../types/complaint";

defineProps<{
  notice: ActionNotice | null;
}>();

const emit = defineEmits<{
  dismiss: [];
}>();
</script>

<template>
  <section v-if="notice" class="notice" :data-tone="notice.tone">
    <p>{{ notice.message }}</p>
    <button type="button" @click="emit('dismiss')">知道了</button>
  </section>
</template>

<style scoped>
.notice {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 18px;
  border-radius: 16px;
  border: 1px solid transparent;
  box-shadow: 0 12px 28px rgba(31, 79, 126, 0.08);
}

.notice[data-tone="info"] {
  background: #eef6ff;
  border-color: #c9ddf1;
  color: #214566;
}

.notice[data-tone="success"] {
  background: #eefaf2;
  border-color: #c7e7d2;
  color: #1f5a37;
}

.notice[data-tone="error"] {
  background: #fff1ef;
  border-color: #efc7c0;
  color: #8a2f2f;
}

p {
  margin: 0;
  line-height: 1.6;
}

button {
  border: 1px solid currentColor;
  border-radius: 12px;
  padding: 8px 12px;
  background: transparent;
  color: inherit;
  font: inherit;
  font-weight: 600;
}
</style>
