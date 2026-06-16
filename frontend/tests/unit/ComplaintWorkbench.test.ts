import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { describe, expect, it } from "vitest";

import ComplaintWorkbench from "../../src/views/ComplaintWorkbench.vue";

describe("ComplaintWorkbench", () => {
  it("renders the task 17 workbench sections", async () => {
    setActivePinia(createPinia());

    const wrapper = mount(ComplaintWorkbench);

    expect(wrapper.text()).toContain("Session Sidebar");
    expect(wrapper.text()).toContain("Complaint Composer");
    expect(wrapper.text()).toContain("Workflow Timeline");
    expect(wrapper.text()).toContain("Solution Panel");
    expect(wrapper.text()).toContain("Evidence Panel");
    expect(wrapper.text()).toContain("Feedback Bar");
  });
});
