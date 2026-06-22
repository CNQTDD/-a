<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { formatFeedbackActionLabel } from "../presentation/complaint-display";
import type { ComplaintSessionState } from "../types/complaint";

const props = defineProps<{
  session: ComplaintSessionState | null;
  pending?: boolean;
}>();

const emit = defineEmits<{
  accept: [];
  edit: [solution: string];
  reject: [reason: string];
  archive: [];
}>();

const mode = ref<"idle" | "edit" | "reject">("idle");
const editedSolution = ref("");
const rejectReason = ref("");

const canArchive = computed(
  () =>
    props.session !== null &&
    (props.session.status === "resolved" || props.session.status === "failed"),
);

watch(
  () => props.session?.finalSolution ?? props.session?.streamedSolution ?? "",
  (solution) => {
    editedSolution.value = solution;
  },
  { immediate: true },
);

function startEdit() {
  mode.value = "edit";
}

function startReject() {
  mode.value = "reject";
}
</script>

<template>
  <section class="panel">
    <p class="eyebrow">人工复核</p>
    <h2>人工反馈</h2>
    <p v-if="session" class="summary">
      当前反馈：{{ session.feedbackAction ? formatFeedbackActionLabel(session.feedbackAction) : "未处理" }}
    </p>
    <div class="actions">
      <button type="button" :disabled="pending || !session" @click="emit('accept')">采纳方案</button>
      <button type="button" :disabled="pending || !session" @click="startEdit">编辑后采纳</button>
      <button type="button" :disabled="pending || !session" @click="startReject">驳回处理</button>
      <button type="button" :disabled="pending || !canArchive" @click="emit('archive')">
        归档会话
      </button>
    </div>

    <div v-if="mode === 'edit'" class="editor">
      <label for="edited-solution">修订后的处置建议</label>
      <textarea id="edited-solution" v-model="editedSolution" rows="4" />
      <button type="button" :disabled="pending || !editedSolution.trim()" @click="emit('edit', editedSolution)">
        提交修订方案
      </button>
    </div>

    <div v-if="mode === 'reject'" class="editor">
      <label for="reject-reason">驳回原因</label>
      <textarea id="reject-reason" v-model="rejectReason" rows="4" />
      <button
        type="button"
        :disabled="pending || !rejectReason.trim()"
        @click="emit('reject', rejectReason)"
      >
        提交驳回
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

h2,
label {
  color: #123252;
}

.actions,
.editor {
  margin-top: 12px;
}

.actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

button {
  border: 1px solid #cad9e8;
  border-radius: 14px;
  padding: 12px 14px;
  background: #f5f9fd;
  color: #16324f;
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
  margin: 8px 0 12px;
  font: inherit;
}

.summary {
  color: #62809f;
}
</style>
