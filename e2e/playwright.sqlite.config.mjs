import { defineConfig } from "@playwright/test";
import path from "node:path";
import os from "node:os";
import fs from "node:fs";

const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");

// Isolated temp directory for sqlite browser smoke — cleaned up per run
const tmpBase = fs.mkdtempSync(path.join(os.tmpdir(), "pw-sqlite-"));
const sqliteDbPath = path.join(tmpBase, "test.db");
// NOTES_DIR stays at the repo default (`data/notes/`) so document-loop
// save/correction/verdict smoke scenarios that assert on saved-note file
// contents behave the same as the JSON-default Playwright path.
const correctionsDir = path.join(tmpBase, "corrections");
const webSearchDir = path.join(tmpBase, "web-search");

export default defineConfig({
  testDir: path.join(repoRoot, "e2e", "tests"),
  testMatch: "web-smoke.spec.mjs",
  timeout: 60_000,
  expect: {
    timeout: 15_000,
  },
  fullyParallel: false,
  retries: 0,
  use: {
    baseURL: "http://127.0.0.1:8880",
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
      + `LOCAL_AI_MOCK_STREAM_DELAY_MS=10 `
      + `LOCAL_AI_STORAGE_BACKEND=sqlite `
      + `LOCAL_AI_SQLITE_DB_PATH=${sqliteDbPath} `
      + `LOCAL_AI_CORRECTIONS_DIR=${correctionsDir} `
      + `LOCAL_AI_WEB_SEARCH_HISTORY_DIR=${webSearchDir} `
      + `python3 -m app.web --host 127.0.0.1 --port 8880'`
    ),
    url: "http://127.0.0.1:8880",
    reuseExistingServer: false,
    timeout: 60_000,
  },
});
