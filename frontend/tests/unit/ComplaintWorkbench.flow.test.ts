import { mount } from "@vue/test-utils";
import { flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { nextTick } from "vue";

const mocks = vi.hoisted(() => ({
  createComplaintSession: vi.fn().mockResolvedValue({
    session_id: "session-42",
  }),
  sendComplaintMessage: vi.fn().mockResolvedValue({ run_id: "run-1" }),
}));

vi.mock("../../src/api/complaints", () => ({
  createComplaintSession: mocks.createComplaintSession,
  sendComplaintMessage: mocks.sendComplaintMessage,
}));

vi.mock("../../src/api/sse", () => ({
  streamEvents: vi.fn(async function* () {
    yield {
      id: "session-42-1",
      event: "workflow_started",
      data: {
        id: "session-42-1",
        sessionId: "session-42",
        sequence: 1,
        type: "workflow_started",
        stage: "intent",
      },
    };
    yield {
      id: "session-42-2",
      event: "intent_completed",
      data: {
        id: "session-42-2",
        sessionId: "session-42",
        sequence: 2,
        type: "intent_completed",
        intent: "billing",
        emotion: "angry",
        entities: ["package", "bill"],
      },
    };
    yield {
      id: "session-42-3",
      event: "retrieval_completed",
      data: {
        id: "session-42-3",
        sessionId: "session-42",
        sequence: 3,
        type: "retrieval_completed",
        evidence: [
          {
            id: "evidence-1",
            sourceType: "business_rule",
            title: "Evidence Item 1",
            contentSnapshot: "套餐账单规则说明",
            score: 0.98,
            articleNumber: "1",
          },
        ],
      },
    };
    yield {
      id: "session-42-4",
      event: "generation_delta",
      data: {
        id: "session-42-4",
        sessionId: "session-42",
        sequence: 4,
        type: "generation_delta",
        delta: "已核对账单并调整套餐费用。",
      },
    };
    yield {
      id: "session-42-5",
      event: "validation_completed",
      data: {
        id: "session-42-5",
        sessionId: "session-42",
        sequence: 5,
        type: "validation_completed",
        validation: {
          status: "passed",
          details: "引用有效",
        },
      },
    };
    yield {
      id: "session-42-6",
      event: "workflow_completed",
      data: {
        id: "session-42-6",
        sessionId: "session-42",
        sequence: 6,
        type: "workflow_completed",
      },
    };
  }),
}));

import ComplaintWorkbench from "../../src/views/ComplaintWorkbench.vue";

describe("ComplaintWorkbench flow", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    mocks.createComplaintSession.mockClear();
    mocks.sendComplaintMessage.mockClear();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("streams intent, evidence, solution, and feedback state", async () => {
    const wrapper = mount(ComplaintWorkbench);

    await wrapper.get("textarea").setValue("我的套餐费用和账单不一致，请帮我核实");
    await wrapper.get("button").trigger("click");
    await flushPromises();
    await new Promise((resolve) => setTimeout(resolve, 0));
    await flushPromises();
    await nextTick();
    await nextTick();

    expect(mocks.createComplaintSession).toHaveBeenCalled();
    expect(mocks.sendComplaintMessage).toHaveBeenCalled();
    expect(wrapper.text()).toContain("Intent: billing");
    expect(wrapper.text()).toContain("Emotion: angry");
    expect(wrapper.text()).toContain("Evidence Item 1");
    expect(wrapper.text()).toContain("Workflow finalized");
    expect(wrapper.text()).toContain("Current feedback: none");
  });
});
