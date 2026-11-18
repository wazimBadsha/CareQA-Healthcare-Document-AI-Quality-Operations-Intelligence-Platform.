import { mkdirSync } from "node:fs";
import { join, resolve } from "node:path";

import { expect, test } from "@playwright/test";

const evidenceRoot = resolve(__dirname, "../../../evidence/2026-11-18/playwright");

function evidencePath(name: string) {
  mkdirSync(evidenceRoot, { recursive: true });
  return join(evidenceRoot, name);
}

test("01 — dashboard loads seeded API-backed workspace", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Evidence for every AI extraction." })).toBeVisible();
  await expect(page.getByText("Live data · synthetic workspace")).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText("Synthetic CareQA benchmark")).toBeVisible();
  await expect(page.getByText("Quality snapshot")).toBeVisible();

  await page.screenshot({ path: evidencePath("01-dashboard-loaded.png"), fullPage: true });
});

test("02 — analyst runs benchmark and inspects persisted field evidence", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Live data · synthetic workspace")).toBeVisible({ timeout: 15_000 });

  await page.getByRole("button", { name: "Run benchmark" }).click();
  await expect(page.getByRole("heading", { name: "Recent outcomes" })).toBeVisible();
  await expect(page.locator("tbody tr").first()).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText("exact match").first()).toBeVisible({ timeout: 15_000 });

  await page.screenshot({ path: evidencePath("02-benchmark-run-and-results.png"), fullPage: true });
});
