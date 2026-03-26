import fs from "node:fs";
import path from "node:path";
import { test, expect } from "@playwright/test";

const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..", "..");
const artifactDir = path.join(repoRoot, "output", "playwright");
const fixtureDir = path.join(artifactDir, "fixtures");
const noteDir = path.join(artifactDir, "notes");
const longFixturePath = path.join(fixtureDir, "long-summary-fixture.md");
const searchFixtureDir = path.join(fixtureDir, "picked-search-folder");
const searchFixtureBudgetPath = path.join(searchFixtureDir, "budget-plan.md");
const searchFixtureMemoPath = path.join(searchFixtureDir, "memo.md");
const initialNotePath = path.join(noteDir, "initial-note.md");
const revisedNotePath = path.join(noteDir, "reissued-note.md");
const directNotePath = path.join(noteDir, "saved-note.md");

function buildSessionId(prefix) {
  return `pw-${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

async function openAdvancedSettings(page) {
  await page.getByTestId("advanced-settings").evaluate((element) => {
    element.open = true;
  });
  await expect(page.getByTestId("session-id")).toBeVisible();
}

async function prepareSession(page, prefix) {
  await openAdvancedSettings(page);
  const sessionId = buildSessionId(prefix);
  await page.getByTestId("session-id").fill(sessionId);
  return sessionId;
}

function ensureLongFixture() {
  fs.mkdirSync(fixtureDir, { recursive: true });
  fs.mkdirSync(noteDir, { recursive: true });
  fs.mkdirSync(searchFixtureDir, { recursive: true });
  const middleSignal = "중간 섹션 핵심 결정은 승인 기반 저장을 유지하는 것입니다.";
  const lines = [
    "# 긴 요약 문서",
    "",
    ...Array.from({ length: 360 }, () => "도입 설명 문장입니다."),
    "",
    "## 핵심 결정",
    middleSignal,
    "추가로 로컬 우선 구조를 유지합니다.",
    "",
    ...Array.from({ length: 360 }, () => "마무리 설명 문장입니다."),
  ];
  fs.writeFileSync(longFixturePath, lines.join("\n"), "utf-8");
  fs.writeFileSync(
    searchFixtureBudgetPath,
    ["# Budget Plan", "", "budget summary", "budget approval draft"].join("\n"),
    "utf-8"
  );
  fs.writeFileSync(
    searchFixtureMemoPath,
    ["# Memo", "", "other notes"].join("\n"),
    "utf-8"
  );
  fs.rmSync(initialNotePath, { force: true });
  fs.rmSync(revisedNotePath, { force: true });
  fs.rmSync(directNotePath, { force: true });
}

test.beforeEach(async ({ page }) => {
  ensureLongFixture();
  await page.goto("/");
});

test("파일 요약 후 근거와 요약 구간이 보입니다", async ({ page }) => {
  await prepareSession(page, "summary");
  await page.getByTestId("source-path").fill(longFixturePath);
  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("response-box")).toContainText("중간 섹션 핵심 결정은 승인 기반 저장을 유지하는 것입니다.");
  await expect(page.getByTestId("evidence-box")).toBeVisible();
  await expect(page.getByTestId("summary-chunks-box")).toBeVisible();

  await page.locator("#toggle-evidence").click();
  await expect(page.locator("#evidence-text")).toContainText("승인 기반 저장");

  await page.locator("#toggle-summary-chunks").click();
  await expect(page.locator("#summary-chunks-text")).toContainText("중간 섹션 핵심 결정은 승인 기반 저장을 유지하는 것입니다.");
  await expect(page.locator("#summary-chunks-hint")).toContainText("대표 구간 3개만 보여줍니다");
  await expect(page.locator("#summary-chunks-text")).toContainText("위치: 전체 12개 중 7번째");
  const scrollState = await page.getByTestId("summary-chunks-scroll-region").evaluate((element) => {
    const target = element;
    const computed = window.getComputedStyle(target);
    return {
      overflowY: computed.overflowY,
      clientHeight: target.clientHeight,
      scrollHeight: target.scrollHeight,
    };
  });
  expect(scrollState.overflowY).toBe("auto");
  expect(scrollState.clientHeight).toBeGreaterThan(0);
});

test("브라우저 파일 선택으로도 파일 요약이 됩니다", async ({ page }) => {
  await prepareSession(page, "picker");
  await page.getByTestId("browser-file-input").setInputFiles(longFixturePath);
  await expect(page.locator("#picked-file-name")).toContainText("long-summary-fixture.md");

  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("response-box")).toContainText("중간 섹션 핵심 결정은 승인 기반 저장을 유지하는 것입니다.");
  await expect(page.locator("#context-box")).toContainText("long-summary-fixture.md");
});

test("브라우저 폴더 선택으로도 문서 검색이 됩니다", async ({ page }) => {
  await prepareSession(page, "folder-search");
  await page.locator('input[name="request_mode"][value="search"]').check();
  await page.getByTestId("browser-folder-input").setInputFiles(searchFixtureDir);
  await expect(page.locator("#picked-folder-name")).toContainText("2개 파일");
  await page.getByTestId("search-query").fill("budget");

  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("response-box")).toContainText("[모의 요약]");
  await expect(page.locator("#selected-text")).toContainText("budget-plan.md");
});

test("저장 요청 후 승인 경로를 다시 발급할 수 있습니다", async ({ page }) => {
  await prepareSession(page, "reissue");
  await page.getByTestId("source-path").fill(longFixturePath);
  await page.getByTestId("save-summary").check();
  await page.getByTestId("note-path").fill(initialNotePath);
  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("approval-box")).toBeVisible();
  await expect(page.getByTestId("approval-path-input")).toHaveValue(initialNotePath);

  await page.getByTestId("approval-path-input").fill(revisedNotePath);
  await page.getByTestId("reissue-button").click();

  await expect(page.getByTestId("response-box")).toContainText("새 경로로 저장하려면 다시 승인해 주세요.");
  await expect(page.getByTestId("approval-path-input")).toHaveValue(revisedNotePath);
});

test("승인 후 실제 note가 저장됩니다", async ({ page }) => {
  await prepareSession(page, "save");
  await page.getByTestId("source-path").fill(longFixturePath);
  await page.getByTestId("save-summary").check();
  await page.getByTestId("note-path").fill(directNotePath);
  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("approval-box")).toBeVisible();
  await page.getByTestId("approve-button").click();

  await expect(page.getByTestId("response-box")).toContainText("저장했습니다.");
  expect(fs.existsSync(directNotePath)).toBeTruthy();
});

test("스트리밍 중 취소 버튼이 동작합니다", async ({ page }) => {
  await prepareSession(page, "cancel");
  await page.getByTestId("source-path").fill(longFixturePath);
  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("cancel-request")).toBeVisible();
  await page.getByTestId("cancel-request").click();

  await expect(page.locator("#notice-box")).toContainText("요청을 취소했습니다.");
});
