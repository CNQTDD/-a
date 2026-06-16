import { expect, test } from "@playwright/test";

test("complaint workbench streams evidence and finalizes feedback", async ({
  page,
}) => {
  await page.goto("/");

  await expect(page.getByText("Complaint Composer")).toBeVisible();
  await page.getByLabel("Complaint text").fill(
    "我的套餐费用和账单不一致，请帮我核实",
  );
  await page.getByRole("button", { name: "Start workflow" }).click();

  await expect(page.getByText("Intent: billing")).toBeVisible();
  await expect(page.getByText("Emotion: angry")).toBeVisible();
  await expect(page.getByText("Evidence Item 1")).toBeVisible();
  await expect(page.getByText("Workflow finalized")).toBeVisible();
  await expect(page.getByRole("button", { name: "Accept" })).toBeVisible();
  await page.getByRole("button", { name: "Accept" }).click();
  await expect(page.getByText("Current feedback: accept")).toBeVisible();
});
