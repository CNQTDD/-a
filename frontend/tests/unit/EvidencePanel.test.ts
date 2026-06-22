import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import EvidencePanel from "../../src/components/EvidencePanel.vue";

describe("EvidencePanel", () => {
  it("renders clean chinese copy for the empty state", () => {
    const wrapper = mount(EvidencePanel, {
      props: {
        evidence: [],
      },
    });

    expect(wrapper.text()).toContain("证据面板");
    expect(wrapper.text()).toContain("暂未检索到证据。");
    expect(wrapper.find("[data-testid='fallback-notice']").exists()).toBe(false);
  });

  it("shows an explicit degraded retrieval notice only for single-path modes", () => {
    const wrapper = mount(EvidencePanel, {
      props: {
        evidence: [],
        degradedSources: ["elasticsearch"],
        retrievalMode: "elasticsearch-only",
      },
    });

    expect(wrapper.get("[data-testid='fallback-notice']").text()).toContain(
      "当前处于 Elasticsearch 单路检索降级模式",
    );
  });

  it("renders evidence metadata in chinese without reporting degradation for balanced mode", () => {
    const wrapper = mount(EvidencePanel, {
      props: {
        evidence: [
          {
            id: "evidence-1",
            sourceType: "business_rule",
            title: "资费争议处理规则",
            contentSnapshot: "账单与套餐不一致时，应优先核查套餐变更记录。",
            score: 0.98,
            articleNumber: "3.2",
          },
        ],
        degradedSources: [],
        retrievalMode: "balanced",
      },
    });

    expect(wrapper.text()).toContain("来源：business_rule");
    expect(wrapper.text()).toContain("条款：3.2");
    expect(wrapper.text()).toContain("分值：0.98");
    expect(wrapper.find("[data-testid='fallback-notice']").exists()).toBe(false);
  });
});
