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
    <p class="eyebrow">投诉受理</p>
    <h2>投诉录入</h2>
    <label for="complaint">投诉内容</label>
    <textarea
      id="complaint"
      :value="props.modelValue"
      rows="5"
      placeholder="请输入用户投诉内容、诉求和关键信息"
      @input="emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
    />
    <div class="actions">
      <button type="button" :disabled="props.busy" @click="emit('submit')">
        {{ props.busy ? "提交中..." : "启动处置流程" }}
      </button>
    </div>
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

label {
  display: block;
  margin-bottom: 8px;
  color: #214566;
  font-weight: 600;
}

textarea {
  width: 100%;
  box-sizing: border-box;
  border-radius: 14px;
  border: 1px solid #c8d8e8;
  background: #f8fbfe;
  color: #16324f;
  padding: 14px;
  resize: vertical;
  font: inherit;
}

.actions {
  margin-top: 14px;
}

button {
  width: 100%;
  border: 1px solid #2f6ea6;
  border-radius: 14px;
  padding: 12px 14px;
  background: linear-gradient(180deg, #4b85bb 0%, #2f6ea6 100%);
  color: #ffffff;
  font-weight: 600;
}
</style>
