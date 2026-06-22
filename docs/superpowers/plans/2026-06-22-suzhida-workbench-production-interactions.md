# SuzhiDa Workbench Production Interactions Implementation Plan

> **For agentic workers:** REQUIRED: Use $subagent-driven-development (if subagents available) or $executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the complaint workbench interactions production-ready with confirmations, action states, retry handling, real feedback submission, and session reuse/archive rules.

**Architecture:** Centralize risky button behavior in the Pinia store and the workbench view, then keep UI components presentation-focused. Add a lightweight confirmation dialog and notice bar so start, feedback, retry, and archive behavior all follow one interaction model.

**Tech Stack:** Vue 3, TypeScript, Pinia, Vitest, Vue Test Utils

---

## File Structure

- Create: `frontend/src/components/ActionConfirmDialog.vue`
- Create: `frontend/src/components/ActionNoticeBar.vue`
- Modify: `frontend/src/types/complaint.ts`
- Modify: `frontend/src/stores/complaint.ts`
- Modify: `frontend/src/api/complaints.ts`
- Modify: `frontend/src/components/ComplaintComposer.vue`
- Modify: `frontend/src/components/FeedbackBar.vue`
- Modify: `frontend/src/components/SessionSidebar.vue`
- Modify: `frontend/src/views/ComplaintWorkbench.vue`
- Test: `frontend/tests/unit/complaint-store.test.ts`
- Test: `frontend/tests/unit/ComplaintWorkbench.flow.test.ts`
- Test: `frontend/tests/unit/ComplaintWorkbench.test.ts`

## Chunk 1: Store And Contract

### Task 1: Add action state contracts

**Files:**
- Modify: `frontend/src/types/complaint.ts`
- Test: `frontend/tests/unit/complaint-store.test.ts`

- [ ] **Step 1: Write the failing test**
- [ ] **Step 2: Run test to verify it fails**
  Run: `vitest run tests/unit/complaint-store.test.ts`
- [ ] **Step 3: Add action state, confirmation, and notice types**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**

### Task 2: Implement store-side interaction governance

**Files:**
- Modify: `frontend/src/stores/complaint.ts`
- Test: `frontend/tests/unit/complaint-store.test.ts`

- [ ] **Step 1: Write the failing test**
- [ ] **Step 2: Run test to verify it fails**
  Run: `vitest run tests/unit/complaint-store.test.ts`
- [ ] **Step 3: Implement pending confirmation, action status, archive visibility, and reuse logic**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**

## Chunk 2: View And Components

### Task 3: Add reusable confirmation and notice components

**Files:**
- Create: `frontend/src/components/ActionConfirmDialog.vue`
- Create: `frontend/src/components/ActionNoticeBar.vue`
- Test: `frontend/tests/unit/ComplaintWorkbench.test.ts`

- [ ] **Step 1: Write the failing test**
- [ ] **Step 2: Run test to verify it fails**
  Run: `vitest run tests/unit/ComplaintWorkbench.test.ts`
- [ ] **Step 3: Implement the minimal shared components**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**

### Task 4: Productionize composer, feedback bar, and sidebar actions

**Files:**
- Modify: `frontend/src/components/ComplaintComposer.vue`
- Modify: `frontend/src/components/FeedbackBar.vue`
- Modify: `frontend/src/components/SessionSidebar.vue`
- Test: `frontend/tests/unit/ComplaintWorkbench.flow.test.ts`

- [ ] **Step 1: Write the failing test**
- [ ] **Step 2: Run test to verify it fails**
  Run: `vitest run tests/unit/ComplaintWorkbench.flow.test.ts`
- [ ] **Step 3: Add disabled states, archive affordance, and risk-action emits**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**

## Chunk 3: Runtime Behavior

### Task 5: Route feedback through real API and action confirmations

**Files:**
- Modify: `frontend/src/api/complaints.ts`
- Modify: `frontend/src/views/ComplaintWorkbench.vue`
- Test: `frontend/tests/unit/ComplaintWorkbench.flow.test.ts`

- [ ] **Step 1: Write the failing test**
- [ ] **Step 2: Run test to verify it fails**
  Run: `vitest run tests/unit/ComplaintWorkbench.flow.test.ts`
- [ ] **Step 3: Implement feedback API mapping and confirmation handling**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**

### Task 6: Add start-workflow auto retry and visible recovery notice

**Files:**
- Modify: `frontend/src/views/ComplaintWorkbench.vue`
- Modify: `frontend/src/stores/complaint.ts`
- Test: `frontend/tests/unit/ComplaintWorkbench.flow.test.ts`

- [ ] **Step 1: Write the failing test**
- [ ] **Step 2: Run test to verify it fails**
  Run: `vitest run tests/unit/ComplaintWorkbench.flow.test.ts`
- [ ] **Step 3: Implement one automatic retry for start flow and visible notice state**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**

## Verification

- [ ] `vitest run tests/unit/complaint-store.test.ts tests/unit/ComplaintWorkbench.test.ts tests/unit/ComplaintWorkbench.flow.test.ts`
- [ ] `tsc --noEmit`
- [ ] `vue-tsc --noEmit`

Plan complete and saved to `docs/superpowers/plans/2026-06-22-suzhida-workbench-production-interactions.md`. Ready to execute.
