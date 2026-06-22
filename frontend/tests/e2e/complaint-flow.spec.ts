import { expect, test } from "@playwright/test";

function sse(events: Array<Record<string, unknown>>): string {
  return events
    .map((event) => `id: ${event.id}\nevent: ${event.type}\ndata: ${JSON.stringify(event)}\n\n`)
    .join("");
}

test("complaint workbench streams evidence and finalizes feedback", async ({ page }) => {
  const sessionId = "session-complaint";
  const complaintText = "我的套餐费用和账单不一致，请帮我核实";

  await page.route("**/api/v1/complaints/sessions", async (route) => {
    if (route.request().method() === "POST") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ session_id: sessionId }),
      });
      return;
    }
    await route.fallback();
  });

  await page.route(`**/api/v1/complaints/${sessionId}/messages`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ run_id: `${sessionId}-run-1` }),
    });
  });

  await page.route(`**/api/v1/complaints/${sessionId}/events`, async (route) => {
    await route.fulfill({
      status: 200,
      headers: {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache, no-transform",
      },
      body: sse([
        {
          id: `${sessionId}-1`,
          sessionId,
          sequence: 1,
          type: "workflow_started",
          stage: "intent",
        },
        {
          id: `${sessionId}-2`,
          sessionId,
          sequence: 2,
          type: "intent_completed",
          intent: "billing",
          emotion: "angry",
          entities: ["套餐", "账单"],
        },
        {
          id: `${sessionId}-3`,
          sessionId,
          sequence: 3,
          type: "retrieval_completed",
          evidence: [
            {
              id: "evidence-1",
              sourceType: "business_rule",
              title: "套餐资费核对规则",
              contentSnapshot: "套餐费用与账单不一致时，需核对生效时间与促销减免记录。",
              score: 0.98,
              articleNumber: "1",
            },
          ],
        },
        {
          id: `${sessionId}-4`,
          sessionId,
          sequence: 4,
          type: "generation_delta",
          delta: "已核对账单与套餐资费，建议补充核销差额并向用户说明。",
        },
        {
          id: `${sessionId}-5`,
          sessionId,
          sequence: 5,
          type: "validation_completed",
          validation: {
            status: "passed",
            details: "证据引用完整",
          },
        },
        {
          id: `${sessionId}-6`,
          sessionId,
          sequence: 6,
          type: "workflow_completed",
        },
      ]),
    });
  });

  await page.route(`**/api/v1/complaints/${sessionId}/feedback`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ id: "feedback-1", session_id: sessionId, action: "accepted" }),
    });
  });

  await page.goto("/");

  await expect(page.getByText("投诉录入")).toBeVisible();
  await page.getByLabel("投诉内容").fill(complaintText);
  await page.getByRole("button", { name: "启动处置流程" }).click();
  await page.getByRole("button", { name: "确认启动" }).click();

  await expect(page.getByTestId("workflow-timeline")).toContainText("意图：", {
    timeout: 10000,
  });
  await expect(page.getByTestId("workflow-timeline")).toContainText("账单争议", {
    timeout: 10000,
  });
  await expect(page.getByTestId("workflow-timeline")).toContainText("情绪：", {
    timeout: 10000,
  });
  await expect(page.getByTestId("workflow-timeline")).toContainText("不满", {
    timeout: 10000,
  });
  await expect(
    page.locator("[data-testid='evidence-panel'] .evidence-list li").first(),
  ).toBeVisible({ timeout: 10000 });
  await expect(page.getByText("暂未检索到证据。")).toHaveCount(0);
  await expect(page.getByText("流程已完成")).toBeVisible({
    timeout: 10000,
  });
  await expect(page.getByRole("button", { name: "采纳方案" })).toBeVisible();

  await page.getByRole("button", { name: "采纳方案" }).click();
  await page.getByRole("button", { name: "确认采纳" }).click();

  await expect(page.getByText("当前反馈：已采纳", { exact: false })).toBeVisible();
});
