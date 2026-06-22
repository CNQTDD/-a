import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { describe, expect, it } from "vitest";

import ComplaintWorkbench from "../../src/views/ComplaintWorkbench.vue";

describe("ComplaintWorkbench", () => {
  it("renders the complaint workbench sections", async () => {
    setActivePinia(createPinia());

    const wrapper = mount(ComplaintWorkbench);

    expect(wrapper.text()).toContain("投诉处置工作台");
    expect(wrapper.text()).toContain("投诉录入");
    expect(wrapper.text()).toContain("流程进度");
    expect(wrapper.text()).toContain("处置建议");
    expect(wrapper.text()).toContain("证据面板");
    expect(wrapper.text()).toContain("人工反馈");
  });
});
