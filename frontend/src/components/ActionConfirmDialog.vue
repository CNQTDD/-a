<script setup lang="ts">
defineProps<{
  open: boolean;
  title: string;
  message: string;
  confirmLabel: string;
  busy?: boolean;
}>();

const emit = defineEmits<{
  cancel: [];
  confirm: [];
}>();
</script>

<template>
  <div v-if="open" class="overlay" role="dialog" aria-modal="true">
    <section class="dialog">
      <p class="eyebrow">操作确认</p>
      <h2>{{ title }}</h2>
      <p class="message">{{ message }}</p>
      <div class="actions">
        <button type="button" class="secondary" :disabled="busy" @click="emit('cancel')">
          取消
        </button>
        <button type="button" class="primary" :disabled="busy" @click="emit('confirm')">
          {{ busy ? "提交中..." : confirmLabel }}
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  background: rgba(19, 41, 63, 0.22);
  backdrop-filter: blur(4px);
  z-index: 20;
}

.dialog {
  width: min(460px, calc(100vw - 32px));
  padding: 24px;
  border-radius: 22px;
  background: #fffdf9;
  border: 1px solid rgba(96, 135, 171, 0.22);
  box-shadow: 0 28px 54px rgba(35, 71, 109, 0.18);
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 0.74rem;
  letter-spacing: 0.12em;
  color: #4f7aa3;
}

h2 {
  margin: 0;
  color: #123252;
}

.message {
  margin: 12px 0 0;
  line-height: 1.7;
  color: #4d6986;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 18px;
}

button {
  border-radius: 14px;
  padding: 10px 16px;
  font: inherit;
  font-weight: 600;
}

.secondary {
  border: 1px solid #c8d8e8;
  background: #f7fbff;
  color: #214566;
}

.primary {
  border: 1px solid #2f6ea6;
  background: linear-gradient(180deg, #4b85bb 0%, #2f6ea6 100%);
  color: #ffffff;
}
</style>
