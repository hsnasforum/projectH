import { defineConfig } from "@playwright/test";
import path from "node:path";

const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");

export default defineConfig({
  testDir: path.join(repoRoot, "e2e", "tests"),
  testMatch: "controller-smoke.spec.mjs",
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  fullyParallel: false,
  retries: 0,
  use: {
    baseURL: "http://127.0.0.1:8781",
    headless: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: `bash -lc 'cd ${repoRoot} && CONTROLLER_PORT=8781 python3 -m controller.server'`,
    url: "http://127.0.0.1:8781/api/runtime/status",
    reuseExistingServer: false,
    timeout: 30_000,
  },
});
