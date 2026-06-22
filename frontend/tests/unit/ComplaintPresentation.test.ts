import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import SessionSidebar from "../../src/components/SessionSidebar.vue";
import SolutionPanel from "../../src/components/SolutionPanel.vue";
import WorkflowTimeline from "../../src/components/WorkflowTimeline.vue";
import type { ComplaintSessionState } from "../../src/types/complaint";

function buildSession(
  overrides: Partial<ComplaintSessionState> = {},
): ComplaintSessionState {
  return {
    id: "session-1",
    complaintText: "我的套餐费用和账单不一致，请帮我核实",
    status: "resolved",
    stage: "resolved",
    intent: "billing_dispute",
    emotion: "angry",
    entities: ["套餐", "账单"],
    riskLevel: "medium",
    degradedSources: ["milvus"],
    retrievalMode: "elasticsearch-only",
    evidence: [],
    streamedSolution: "已核查账单并确认存在重复扣费。",
    finalSolution: "已核查账单并确认存在重复扣费。",
    validation: {
      status: "passed",
      details: "引用完整",
    },
    feedbackAction: "accept",
    feedbackReason: "",
    workflowError: "",
    lastSequence: 6,
    archived: false,
    ...overrides,
  };
}

describe("complaint presentation", () => {
  it("renders workflow labels in business chinese copy", () => {
    const wrapper = mount(WorkflowTimeline, {
      props: {
        session: buildSession(),
      },
    });

    expect(wrapper.text()).toContain("状态： 已完成");
    expect(wrapper.text()).toContain("阶段： 已完成");
    expect(wrapper.text()).toContain("校验结果： 通过 - 引用完整");
    expect(wrapper.text()).toContain("反馈动作： 已采纳");
    expect(wrapper.text()).toContain("降级来源： 向量检索");
  });

  it("renders session stage and empty states in chinese copy", () => {
    const wrapper = mount(SessionSidebar, {
      props: {
        sessions: [buildSession()],
        activeSessionId: "session-1",
      },
    });

    expect(wrapper.text()).toContain("已完成");
    expect(wrapper.text()).not.toContain("resolved");
  });

  it("renders solution validation status in chinese copy", () => {
    const wrapper = mount(SolutionPanel, {
      props: {
        session: buildSession(),
      },
    });

    expect(wrapper.text()).toContain("校验结果：通过 - 引用完整");
    expect(wrapper.text()).not.toContain("passed");
  });
});
