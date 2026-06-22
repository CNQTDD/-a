import { expect, test } from "@playwright/test";

function sse(events: Array<Record<string, unknown>>): string {
  return events
    .map((event) => `id: ${event.id}\nevent: ${event.type}\ndata: ${JSON.stringify(event)}\n\n`)
    .join("");
}

test("degraded retrieval routes the workbench to manual handling", async ({ page }) => {
  const sessionId = "session-degraded";

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
          entities: ["package", "bill"],
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
              title: "Billing rule",
              contentSnapshot: "套餐扣费核查规则",
              score: 0.98,
              articleNumber: "1",
            },
          ],
          degradedSources: ["milvus"],
          retrievalMode: "elasticsearch-only",
        },
        {
          id: `${sessionId}-4`,
          sessionId,
          sequence: 4,
          type: "workflow_failed",
          reason: "Milvus unavailable, Elasticsearch-only fallback active",
        },
      ]),
    });
  });

  await page.goto("/");
  await page.getByLabel("投诉内容").fill("请帮我核查套餐扣费");
  await page.getByRole("button", { name: "启动处置流程" }).click();
  await page.getByRole("button", { name: "确认启动" }).click();

  await expect(page.getByTestId("fallback-notice")).toContainText("Elasticsearch");
  await expect(page.getByText("需要人工兜底处理", { exact: true })).toBeVisible();
  await expect(page.getByTestId("workflow-timeline")).toContainText(
    "流程异常： Milvus unavailable, Elasticsearch-only fallback active",
  );
  await expect(page.getByText("Billing rule")).toBeVisible();
  await expect(page.getByText("Evidence Item", { exact: false })).toHaveCount(0);
});
