import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 30_000,
  outputDir: "../../evidence/2026-11-18/playwright/test-output",
  reporter: [
    ["list"],
    ["html", { outputFolder: "../../evidence/2026-11-18/playwright/report", open: "never" }]
  ],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure"
  }
});
