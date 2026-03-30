import { defineConfig } from "@playwright/test";
import path from "node:path";

const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");

export default defineConfig({
  testDir: path.join(repoRoot, "e2e", "tests"),
  timeout: 60_000,
  expect: {
    timeout: 15_000,
  },
  fullyParallel: false,
  retries: 0,
  use: {
    baseURL: "http://127.0.0.1:8879",
    headless: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: (
      `bash -lc 'cd ${repoRoot} && `
      + `env -u LOCAL_AI_MODEL_PROVIDER -u LOCAL_AI_OLLAMA_MODEL `
      + `LOCAL_AI_MODEL_PROVIDER=mock `
      + `LOCAL_AI_OLLAMA_MODEL= `
      + `LOCAL_AI_MOCK_STREAM_DELAY_MS=80 `
      + `python3 -m app.web --host 127.0.0.1 --port 8879'`
    ),
    url: "http://127.0.0.1:8879",
    reuseExistingServer: false,
    timeout: 60_000,
  },
});
