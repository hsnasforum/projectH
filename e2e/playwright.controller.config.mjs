import { defineConfig } from "@playwright/test";
import path from "node:path";

const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const port = process.env.CONTROLLER_SMOKE_PORT || "8781";

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
    baseURL: `http://127.0.0.1:${port}`,
    headless: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: `bash -lc 'cd ${repoRoot} && CONTROLLER_PORT=${port} python3 -m controller.server'`,
    url: `http://127.0.0.1:${port}/api/runtime/status`,
    reuseExistingServer: false,
    timeout: 30_000,
  },
});
