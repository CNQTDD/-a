<script setup lang="ts">
import { ref, watch } from "vue";

import type { ComplaintSessionState } from "../types/complaint";

const props = defineProps<{
  session: ComplaintSessionState | null;
  pending?: boolean;
}>();

const emit = defineEmits<{
  accept: [];
  edit: [solution: string];
  reject: [reason: string];
}>();

const mode = ref<"idle" | "edit" | "reject">("idle");
const editedSolution = ref("");
const rejectReason = ref("");

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
    <p class="eyebrow">Feedback Bar</p>
    <h2>Operator action</h2>
    <p v-if="session" class="summary">
      Current feedback: {{ session.feedbackAction || "none" }}
    </p>
    <div class="actions">
      <button type="button" :disabled="pending || !session" @click="emit('accept')">
        Accept
      </button>
      <button type="button" :disabled="pending || !session" @click="startEdit">
        Edit
      </button>
      <button type="button" :disabled="pending || !session" @click="startReject">
        Reject
      </button>
    </div>

    <div v-if="mode === 'edit'" class="editor">
      <label for="edited-solution">Edited solution</label>
      <textarea id="edited-solution" v-model="editedSolution" rows="4" />
      <button type="button" :disabled="pending" @click="emit('edit', editedSolution)">
        Submit edited solution
      </button>
    </div>

    <div v-if="mode === 'reject'" class="editor">
      <label for="reject-reason">Reject reason</label>
      <textarea id="reject-reason" v-model="rejectReason" rows="4" />
      <button type="button" :disabled="pending || !rejectReason.trim()" @click="emit('reject', rejectReason)">
        Submit rejection
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
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.05);
  color: inherit;
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
  margin: 8px 0 12px;
}

.summary {
  color: rgba(244, 239, 231, 0.72);
}
</style>
