<script setup lang="ts">
const props = defineProps<{
  modelValue: string;
  busy?: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
  submit: [];
}>();
</script>

<template>
  <section class="panel">
    <p class="eyebrow">Complaint Composer</p>
    <h2>Case intake</h2>
    <label for="complaint">Complaint text</label>
    <textarea
      id="complaint"
      :value="props.modelValue"
      rows="5"
      @input="emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
    />
    <div class="actions">
      <button type="button" :disabled="props.busy" @click="emit('submit')">
        Start workflow
      </button>
    </div>
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

label {
  display: block;
  margin-bottom: 8px;
}

textarea {
  width: 100%;
  box-sizing: border-box;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(17, 19, 22, 0.92);
  color: inherit;
  padding: 14px;
  resize: vertical;
}

.actions {
  margin-top: 14px;
}

button {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.05);
  color: inherit;
}
</style>
