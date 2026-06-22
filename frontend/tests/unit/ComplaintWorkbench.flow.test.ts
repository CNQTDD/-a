import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { nextTick } from "vue";

const mocks = vi.hoisted(() => ({
  createComplaintSession: vi.fn().mockResolvedValue({
    id: "session-42",
  }),
  sendComplaintMessage: vi.fn().mockResolvedValue({ run_id: "run-1" }),
  submitComplaintFeedback: vi.fn().mockResolvedValue({
    id: "feedback-1",
    action: "accepted",
  }),
  streamEvents: vi.fn(async function* () {
    yield {
      id: "evt-1",
      event: "workflow_started",
      data: {
        message: "workflow started",
      },
    };
    yield {
      id: "evt-2",
      event: "intent_completed",
      data: {
        intent: "billing",
        emotion: "angry",
        entities: ["package", "bill"],
      },
    };
    yield {
      id: "evt-3",
      event: "retrieval_completed",
      data: {
        evidence: [
          {
            evidence_id: "evidence-1",
            source_id: "policy-1",
            source_type: "business_rule",
            title: "证据条目 1",
            content_snapshot: "套餐账单规则说明",
            score: 0.98,
            article: "1",
          },
        ],
      },
    };
    yield {
      id: "evt-4",
      event: "generation_delta",
      data: {
        text: "已核对账单并调整套餐费用。",
      },
    };
    yield {
      id: "evt-5",
      event: "validation_completed",
      data: {
        status: "passed",
        details: "引用有效",
      },
    };
    yield {
      id: "evt-6",
      event: "workflow_completed",
      data: {
        status: "waiting_human",
      },
    };
  }),
}));

vi.mock("../../src/api/complaints", () => ({
  createComplaintSession: mocks.createComplaintSession,
  sendComplaintMessage: mocks.sendComplaintMessage,
  submitComplaintFeedback: mocks.submitComplaintFeedback,
}));

vi.mock("../../src/api/sse", () => ({
  streamEvents: mocks.streamEvents,
}));

import ComplaintWorkbench from "../../src/views/ComplaintWorkbench.vue";
import { useComplaintStore } from "../../src/stores/complaint";

describe("ComplaintWorkbench flow", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    mocks.createComplaintSession.mockReset();
    mocks.createComplaintSession.mockResolvedValue({ id: "session-42" });
    mocks.sendComplaintMessage.mockReset();
    mocks.sendComplaintMessage.mockResolvedValue({ run_id: "run-1" });
    mocks.submitComplaintFeedback.mockReset();
    mocks.submitComplaintFeedback.mockResolvedValue({ id: "feedback-1", action: "accepted" });
    mocks.streamEvents.mockReset();
    mocks.streamEvents.mockImplementation(async function* () {
      yield {
        id: "evt-1",
        event: "workflow_started",
        data: {
          message: "workflow started",
        },
      };
      yield {
        id: "evt-2",
        event: "intent_completed",
        data: {
          intent: "billing",
          emotion: "angry",
          entities: ["package", "bill"],
        },
      };
      yield {
        id: "evt-3",
        event: "retrieval_completed",
        data: {
          evidence: [
            {
              evidence_id: "evidence-1",
              source_id: "policy-1",
              source_type: "business_rule",
              title: "证据条目 1",
              content_snapshot: "套餐账单规则说明",
              score: 0.98,
              article: "1",
            },
          ],
        },
      };
      yield {
        id: "evt-4",
        event: "generation_delta",
        data: {
          text: "已核对账单并调整套餐费用。",
        },
      };
      yield {
        id: "evt-5",
        event: "validation_completed",
        data: {
          status: "passed",
          details: "引用有效",
        },
      };
      yield {
        id: "evt-6",
        event: "workflow_completed",
        data: {
          status: "waiting_human",
        },
      };
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  async function clickButtonByText(wrapper: ReturnType<typeof mount>, text: string) {
    const button = wrapper.findAll("button").find((candidate) => candidate.text().includes(text));
    if (!button) {
      throw new Error(`missing button: ${text}`);
    }
    await button.trigger("click");
  }

  async function confirmVisibleAction(wrapper: ReturnType<typeof mount>) {
    await clickButtonByText(wrapper, "确认");
  }

  it("requires confirmation before starting the workflow", async () => {
    const wrapper = mount(ComplaintWorkbench);

    await wrapper.get("textarea").setValue("我的套餐费用和账单不一致，请帮我核实");
    await clickButtonByText(wrapper, "启动处置流程");
    await flushPromises();

    expect(wrapper.text()).toContain("确认启动处置流程");
    expect(mocks.createComplaintSession).not.toHaveBeenCalled();

    await confirmVisibleAction(wrapper);
    await flushPromises();
    await nextTick();

    expect(mocks.createComplaintSession).toHaveBeenCalledOnce();
    expect(mocks.sendComplaintMessage).toHaveBeenCalledOnce();
  });

  it("automatically retries the start workflow action once after a recoverable error", async () => {
    mocks.createComplaintSession
      .mockRejectedValueOnce(new Error("temporary network error"))
      .mockResolvedValueOnce({ id: "session-42" });

    const wrapper = mount(ComplaintWorkbench);

    await wrapper.get("textarea").setValue("我的套餐费用和账单不一致，请帮我核实");
    await clickButtonByText(wrapper, "启动处置流程");
    await flushPromises();
    await confirmVisibleAction(wrapper);
    await flushPromises();
    await nextTick();
    await nextTick();

    expect(mocks.createComplaintSession).toHaveBeenCalledTimes(2);
    expect(wrapper.text()).toContain("自动重试一次");
  });

  it("sends confirmed feedback through the backend API", async () => {
    const wrapper = mount(ComplaintWorkbench);

    await wrapper.get("textarea").setValue("我的套餐费用和账单不一致，请帮我核实");
    await clickButtonByText(wrapper, "启动处置流程");
    await flushPromises();
    await confirmVisibleAction(wrapper);
    await flushPromises();
    await new Promise((resolve) => setTimeout(resolve, 0));
    await flushPromises();

    await clickButtonByText(wrapper, "采纳方案");
    await flushPromises();

    expect(wrapper.text()).toContain("确认采纳方案");

    await confirmVisibleAction(wrapper);
    await flushPromises();

    expect(mocks.submitComplaintFeedback).toHaveBeenCalledWith(
      expect.any(String),
      "session-42",
      expect.objectContaining({
        action: "accepted",
      }),
      expect.objectContaining({
        idempotencyKey: expect.any(String),
      }),
    );
  });

  it("does not create a new session when the same unfinished complaint already exists", async () => {
    const wrapper = mount(ComplaintWorkbench);
    const complaintText = "我的套餐费用和账单不一致，请帮我核实";

    await wrapper.get("textarea").setValue(complaintText);
    await clickButtonByText(wrapper, "启动处置流程");
    await flushPromises();
    await confirmVisibleAction(wrapper);
    await flushPromises();
    await new Promise((resolve) => setTimeout(resolve, 0));
    await flushPromises();

    expect(mocks.createComplaintSession).toHaveBeenCalledTimes(1);
    expect(mocks.sendComplaintMessage).toHaveBeenCalledTimes(1);

    await clickButtonByText(wrapper, "启动处置流程");
    await flushPromises();
    await confirmVisibleAction(wrapper);
    await flushPromises();

    expect(mocks.createComplaintSession).toHaveBeenCalledTimes(1);
    expect(mocks.sendComplaintMessage).toHaveBeenCalledTimes(1);
  });

  it("archives a resolved session only after explicit confirmation", async () => {
    const wrapper = mount(ComplaintWorkbench);
    const store = useComplaintStore();

    store.createSession({
      id: "session-archive",
      complaintText: "网络长时间没有恢复，要求赔偿",
    });
    store.sessions["session-archive"].status = "resolved";
    store.sessions["session-archive"].stage = "resolved";
    store.activeSessionId = "session-archive";
    await nextTick();

    await clickButtonByText(wrapper, "归档会话");
    await flushPromises();

    expect(wrapper.text()).toContain("确认归档会话");

    await confirmVisibleAction(wrapper);
    await flushPromises();

    expect(store.sessions["session-archive"].archived).toBe(true);
  });

  it("shows an actionable error notice when the workflow falls back to manual handling", async () => {
    const failedStreamImplementation = (async function* () {
      yield {
        id: "evt-1",
        event: "workflow_started",
        data: {
          message: "workflow started",
        },
      };
      yield {
        id: "evt-2",
        event: "workflow_failed",
        data: {
          reason: "Milvus unavailable, Elasticsearch-only fallback active",
        },
      };
    }) as NonNullable<Parameters<typeof mocks.streamEvents.mockImplementationOnce>[0]>;
    mocks.streamEvents.mockImplementationOnce(failedStreamImplementation);

    const wrapper = mount(ComplaintWorkbench);

    await wrapper.get("textarea").setValue("网络长时间没有恢复，要求赔偿");
    await clickButtonByText(wrapper, "启动处置流程");
    await flushPromises();
    await confirmVisibleAction(wrapper);
    await flushPromises();

    expect(wrapper.text()).toContain("流程转入人工兜底");
    expect(wrapper.text()).toContain("Milvus unavailable, Elasticsearch-only fallback active");
  });
});
