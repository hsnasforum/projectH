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
const lateFlipNotePath = path.join(noteDir, "late-flip-note.md");
const rejectedVerdictNotePath = path.join(noteDir, "rejected-verdict-note.md");
const correctedBridgeNotePath = path.join(repoRoot, "data", "notes", "long-summary-fixture-summary.md");
const middleSignal = "중간 섹션 핵심 결정은 승인 기반 저장을 유지하는 것입니다.";
const shortFixturePath = path.join(fixtureDir, "short-aggregate-fixture.md");

function buildSessionId(prefix) {
  return `pw-${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

async function fetchSessionPayload(page, sessionId) {
  const response = await page.request.get(`/api/session?session_id=${encodeURIComponent(sessionId)}`);
  expect(response.ok()).toBeTruthy();
  return await response.json();
}

function findLatestCandidateSourceMessage(messages) {
  return [...(Array.isArray(messages) ? messages : [])]
    .reverse()
    .find(
      (message) => message && message.session_local_candidate && typeof message.session_local_candidate === "object"
    );
}

function findMessageById(messages, messageId) {
  const normalizedMessageId = String(messageId || "");
  return (Array.isArray(messages) ? messages : []).find(
    (message) => message && String(message.message_id || "") === normalizedMessageId
  );
}

async function openAdvancedSettings(page) {
  await page.getByTestId("advanced-settings").evaluate((element) => {
    element.open = true;
  });
  await expect(page.getByTestId("session-id")).toBeVisible();
}

async function prepareSession(page, prefix) {
  await page.locator("#new-session").click();
  await openAdvancedSettings(page);
  const sessionId = buildSessionId(prefix);
  await page.getByTestId("session-id").fill(sessionId);
  await expect(page.getByTestId("approval-box")).toBeHidden();
  return sessionId;
}

function ensureLongFixture() {
  fs.mkdirSync(fixtureDir, { recursive: true });
  fs.mkdirSync(noteDir, { recursive: true });
  fs.mkdirSync(searchFixtureDir, { recursive: true });
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
  const shortLines = [
    "# 짧은 요약 문서",
    "",
    ...Array.from({ length: 6 }, () => "도입 설명 문장입니다."),
    "",
    "## 핵심 결정",
    middleSignal,
    "추가로 로컬 우선 구조를 유지합니다.",
    "",
    ...Array.from({ length: 6 }, () => "마무리 설명 문장입니다."),
  ];
  fs.writeFileSync(shortFixturePath, shortLines.join("\n"), "utf-8");
  fs.writeFileSync(
    searchFixtureBudgetPath,
    ["# Budget Plan", "", "budget summary", "budget approval draft"].join("\n"),
    "utf-8"
  );
  fs.writeFileSync(
    searchFixtureMemoPath,
    ["# Memo", "", "other notes", "budget reference"].join("\n"),
    "utf-8"
  );
  fs.mkdirSync(path.dirname(correctedBridgeNotePath), { recursive: true });
  fs.rmSync(initialNotePath, { force: true });
  fs.rmSync(revisedNotePath, { force: true });
  fs.rmSync(directNotePath, { force: true });
  fs.rmSync(lateFlipNotePath, { force: true });
  fs.rmSync(rejectedVerdictNotePath, { force: true });
  fs.rmSync(correctedBridgeNotePath, { force: true });
}

test.beforeEach(async ({ page }) => {
  ensureLongFixture();
  await page.goto("/");
  await page.waitForLoadState("networkidle");
});

test("파일 요약 후 근거와 요약 구간이 보입니다", async ({ page }) => {
  await prepareSession(page, "summary");
  await expect(page.getByTestId("response-copy-text")).toBeHidden();
  const notePlaceholder = await page.getByTestId("note-path").getAttribute("placeholder");
  expect(notePlaceholder).toContain("data/notes");
  await page.getByTestId("source-path").fill(longFixturePath);
  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("response-box")).toContainText("중간 섹션 핵심 결정은 승인 기반 저장을 유지하는 것입니다.");
  await expect(page.locator("#response-quick-meta-text")).toContainText("long-summary-fixture.md");
  await expect(page.locator("#response-quick-meta-text")).toContainText("문서 요약");
  await expect(page.getByTestId("response-copy-text")).toBeVisible();
  await expect(page.locator("#transcript .message-when")).toHaveCount(2);
  await expect(page.locator("#transcript .message-when").first()).not.toBeEmpty();
  await expect(page.locator('#transcript [data-testid="transcript-meta"]').last()).toContainText("문서 요약");
  await expect(page.locator('#transcript [data-testid="transcript-meta"]').last()).toContainText("long-summary-fixture.md");
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

  await page.getByTestId("source-path").fill(longFixturePath);
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-copy-text")).toBeHidden();
  await expect(page.getByTestId("response-box")).toContainText(middleSignal);
  await expect(page.getByTestId("response-copy-text")).toBeVisible();

  await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.getByTestId("response-copy-text").click();
  await expect(page.locator("#notice-box")).toContainText("본문을 복사했습니다.");
  const clipboardText = await page.evaluate(() => navigator.clipboard.readText());
  expect(clipboardText).toContain(middleSignal);
});

test("브라우저 파일 선택으로도 파일 요약이 됩니다", async ({ page }) => {
  await prepareSession(page, "picker");
  await page.getByTestId("browser-file-input").setInputFiles(longFixturePath);
  await expect(page.locator("#picked-file-name")).toContainText("long-summary-fixture.md");

  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("response-box")).toContainText("중간 섹션 핵심 결정은 승인 기반 저장을 유지하는 것입니다.");
  await expect(page.locator("#context-box")).toContainText("long-summary-fixture.md");
  await expect(page.locator("#response-quick-meta-text")).toContainText("long-summary-fixture.md");
  await expect(page.locator("#response-quick-meta-text")).toContainText("문서 요약");
  await expect(page.locator('#transcript [data-testid="transcript-meta"]').last()).toContainText("long-summary-fixture.md");
  await expect(page.locator('#transcript [data-testid="transcript-meta"]').last()).toContainText("문서 요약");
});

test("브라우저 폴더 선택으로도 문서 검색이 됩니다", async ({ page }) => {
  await prepareSession(page, "folder-search");
  await page.locator('input[name="request_mode"][value="search"]').check();
  await page.getByTestId("browser-folder-input").setInputFiles(searchFixtureDir);
  await expect(page.locator("#picked-folder-name")).toContainText("2개 파일");
  await page.getByTestId("search-query").fill("budget");

  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("response-box")).toContainText("[모의 요약]");
  await expect(page.locator("#response-quick-meta-text")).toContainText("선택 결과 요약");
  await expect(page.locator("#response-quick-meta-text")).toContainText("출처 2개");
  await expect(page.locator("#response-quick-meta-text")).not.toContainText(/출처\s+budget-plan\.md/);
  await expect(page.locator("#response-quick-meta-text")).not.toContainText(/출처\s+memo\.md/);
  await expect(page.locator('#transcript [data-testid="transcript-meta"]').last()).toContainText("선택 결과 요약");
  await expect(page.locator('#transcript [data-testid="transcript-meta"]').last()).toContainText("출처 2개");
  await expect(page.locator('#transcript [data-testid="transcript-meta"]').last()).not.toContainText(/출처\s+budget-plan\.md/);
  await expect(page.locator('#transcript [data-testid="transcript-meta"]').last()).not.toContainText(/출처\s+memo\.md/);
  await expect(page.locator("#selected-text")).toContainText("budget-plan.md");

  // response detail preview panel is visible alongside summary body
  await expect(page.getByTestId("response-search-preview")).toBeVisible();
  await expect(page.locator("#response-search-preview .search-preview-item")).toHaveCount(2);
  await expect(page.locator("#response-search-preview .search-preview-name").first()).toContainText("budget-plan.md");
  await expect(page.locator("#response-search-preview .search-preview-name").first()).toHaveAttribute("title", /.*\/budget-plan\.md$/);
  await expect(page.locator("#response-search-preview .search-preview-match").first()).toContainText("파일명 일치");
  await expect(page.locator("#response-search-preview .search-preview-snippet").first()).toBeVisible();
  await expect(page.locator("#response-search-preview .search-preview-snippet").first()).toContainText("budget-plan");
  await expect(page.locator("#response-search-preview .search-preview-name").nth(1)).toContainText("memo.md");
  await expect(page.locator("#response-search-preview .search-preview-name").nth(1)).toHaveAttribute("title", /.*\/memo\.md$/);
  await expect(page.locator("#response-search-preview .search-preview-match").nth(1)).toContainText("내용 일치");
  await expect(page.locator("#response-search-preview .search-preview-snippet").nth(1)).toBeVisible();
  await expect(page.locator("#response-search-preview .search-preview-snippet").nth(1)).toContainText("budget");
  await expect(page.getByTestId("response-text")).toBeVisible();

  // transcript preview panel is also visible in search-plus-summary
  const lastAssistant = page.locator("#transcript .message.assistant").last();
  await expect(lastAssistant.locator(".search-preview-panel")).toBeVisible();
  await expect(lastAssistant.locator(".search-preview-item")).toHaveCount(2);
  await expect(lastAssistant.locator(".search-preview-name").first()).toContainText("budget-plan.md");
  await expect(lastAssistant.locator(".search-preview-name").first()).toHaveAttribute("title", /.*\/budget-plan\.md$/);
  await expect(lastAssistant.locator(".search-preview-match").first()).toContainText("파일명 일치");
  await expect(lastAssistant.locator(".search-preview-snippet").first()).toBeVisible();
  await expect(lastAssistant.locator(".search-preview-snippet").first()).toContainText("budget-plan");
  await expect(lastAssistant.locator(".search-preview-name").nth(1)).toContainText("memo.md");
  await expect(lastAssistant.locator(".search-preview-name").nth(1)).toHaveAttribute("title", /.*\/memo\.md$/);
  await expect(lastAssistant.locator(".search-preview-match").nth(1)).toContainText("내용 일치");
  await expect(lastAssistant.locator(".search-preview-snippet").nth(1)).toBeVisible();
  await expect(lastAssistant.locator(".search-preview-snippet").nth(1)).toContainText("budget");
});

test("검색만 응답은 transcript에서 preview cards만 보이고 본문 텍스트는 숨겨집니다", async ({ page }) => {
  await prepareSession(page, "search-only");
  await page.locator('input[name="request_mode"][value="search"]').check();
  await page.getByTestId("browser-folder-input").setInputFiles(searchFixtureDir);
  await expect(page.locator("#picked-folder-name")).toContainText("2개 파일");
  await page.getByTestId("search-query").fill("budget");
  await page.locator("#search-only").check();

  await page.getByTestId("submit-request").click();

  // response detail box shows preview cards instead of raw text
  await expect(page.getByTestId("response-search-preview")).toBeVisible();
  await expect(page.locator("#response-search-preview .search-preview-item")).toHaveCount(2);
  await expect(page.locator("#response-search-preview .search-preview-name").first()).toContainText("budget-plan.md");
  await expect(page.locator("#response-search-preview .search-preview-name").first()).toContainText("1. budget-plan.md");
  await expect(page.locator("#response-search-preview .search-preview-name").first()).toHaveAttribute("title", /.*\/budget-plan\.md$/);
  await expect(page.locator("#response-search-preview .search-preview-match").first()).toContainText("파일명 일치");
  await expect(page.locator("#response-search-preview .search-preview-snippet").first()).toBeVisible();
  await expect(page.locator("#response-search-preview .search-preview-snippet").first()).toContainText("budget-plan");
  await expect(page.locator("#response-search-preview .search-preview-name").nth(1)).toContainText("memo.md");
  await expect(page.locator("#response-search-preview .search-preview-name").nth(1)).toContainText("2. memo.md");
  await expect(page.locator("#response-search-preview .search-preview-name").nth(1)).toHaveAttribute("title", /.*\/memo\.md$/);
  await expect(page.locator("#response-search-preview .search-preview-match").nth(1)).toContainText("내용 일치");
  await expect(page.locator("#response-search-preview .search-preview-snippet").nth(1)).toBeVisible();
  await expect(page.locator("#response-search-preview .search-preview-snippet").nth(1)).toContainText("budget");
  await expect(page.getByTestId("response-text")).toBeHidden();
  await expect(page.getByTestId("response-copy-text")).toBeHidden();
  await expect(page.locator("#selected-text")).toContainText("budget-plan.md");

  // selected-copy button is visible and copies path list
  await expect(page.getByTestId("selected-copy")).toBeVisible();
  await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.getByTestId("selected-copy").click();
  await expect(page.locator("#notice-box")).toContainText("선택 경로를 복사했습니다.");
  const clipboardText = await page.evaluate(() => navigator.clipboard.readText());
  expect(clipboardText).toContain("budget-plan.md");

  // transcript preview cards are visible
  const lastAssistant = page.locator("#transcript .message.assistant").last();
  await expect(lastAssistant.locator(".search-preview-panel")).toBeVisible();
  await expect(lastAssistant.locator(".search-preview-item")).toHaveCount(2);
  await expect(lastAssistant.locator(".search-preview-name").first()).toContainText("budget-plan.md");
  await expect(lastAssistant.locator(".search-preview-name").first()).toContainText("1. budget-plan.md");
  await expect(lastAssistant.locator(".search-preview-name").first()).toHaveAttribute("title", /.*\/budget-plan\.md$/);
  await expect(lastAssistant.locator(".search-preview-match").first()).toContainText("파일명 일치");
  await expect(lastAssistant.locator(".search-preview-snippet").first()).toBeVisible();
  await expect(lastAssistant.locator(".search-preview-snippet").first()).toContainText("budget-plan");
  await expect(lastAssistant.locator(".search-preview-name").nth(1)).toContainText("memo.md");
  await expect(lastAssistant.locator(".search-preview-name").nth(1)).toHaveAttribute("title", /.*\/memo\.md$/);
  await expect(lastAssistant.locator(".search-preview-match").nth(1)).toContainText("내용 일치");
  await expect(lastAssistant.locator(".search-preview-snippet").nth(1)).toBeVisible();
  await expect(lastAssistant.locator(".search-preview-snippet").nth(1)).toContainText("budget");

  // transcript body text (pre) should be hidden for search-only
  await expect(lastAssistant.locator("pre")).toHaveCount(0);

  // after search-only, send search-plus-summary in same session — body must recover
  await page.locator("#search-only").uncheck();
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-box")).toContainText("[모의 요약]");
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-search-preview")).toBeVisible();
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

test("원문 저장 후 늦게 내용 거절해도 saved history와 latest verdict가 분리됩니다", async ({ page }) => {
  await prepareSession(page, "late-flip");
  await page.getByTestId("source-path").fill(longFixturePath);
  await page.getByTestId("save-summary").check();
  await page.getByTestId("note-path").fill(lateFlipNotePath);
  await page.getByTestId("submit-request").click();

  const responseBox = page.getByTestId("response-box");

  await expect(page.getByTestId("approval-box")).toBeVisible();
  await page.getByTestId("approve-button").click();

  await expect(responseBox).toContainText("저장했습니다.");
  await expect(page.locator("#response-saved-path-row")).toBeVisible();
  await expect(page.locator("#response-saved-path")).toContainText("late-flip-note.md");
  await expect(page.locator("#response-content-verdict-state")).toContainText("최신 내용 판정은 원문 저장 승인입니다.");
  await expect(page.getByTestId("response-content-reason-box")).toBeHidden();
  expect(fs.existsSync(lateFlipNotePath)).toBeTruthy();
  const savedBeforeReject = fs.readFileSync(lateFlipNotePath, "utf-8");
  expect(savedBeforeReject).toContain("중간 섹션 핵심 결정은 승인 기반 저장을 유지하는 것입니다.");

  await page.getByTestId("response-content-reject").click();

  await expect(responseBox).toContainText("저장했습니다.");
  await expect(page.locator("#notice-box")).toContainText("이미 저장된 노트는 그대로 유지되며 최신 내용 판정만 바뀝니다.");
  await expect(page.locator("#response-content-verdict-state")).toContainText("내용 거절 기록됨");
  await expect(page.locator("#response-content-verdict-status")).toContainText("이미 저장된 노트와 경로는 그대로 남고, 이번 내용 거절은 최신 판정만 바꿉니다.");
  await expect(page.getByTestId("response-content-reason-box")).toBeVisible();
  await expect(page.locator("#response-saved-path-row")).toBeVisible();
  await expect(page.locator("#response-saved-path")).toContainText("late-flip-note.md");
  expect(fs.readFileSync(lateFlipNotePath, "utf-8")).toBe(savedBeforeReject);
});

test("내용 거절은 approval을 유지하고 나중 explicit save로 supersede 됩니다", async ({ page }) => {
  const rejectNote = "핵심 결론이 문서 문맥과 다릅니다.";
  const sessionId = await prepareSession(page, "rejected-verdict");
  await page.getByTestId("source-path").fill(longFixturePath);
  await page.getByTestId("save-summary").check();
  await page.getByTestId("note-path").fill(rejectedVerdictNotePath);
  await page.getByTestId("submit-request").click();

  const responseBox = page.getByTestId("response-box");
  const approvalBox = page.getByTestId("approval-box");

  await expect(responseBox).toContainText("중간 섹션 핵심 결정은 승인 기반 저장을 유지하는 것입니다.");
  await expect(approvalBox).toBeVisible();
  await expect(responseBox.getByTestId("response-content-verdict-box")).toBeVisible();
  await expect(responseBox.getByTestId("response-content-reject")).toBeVisible();
  await expect(responseBox.getByTestId("response-content-reason-box")).toBeHidden();
  await expect(approvalBox.locator('[data-testid="response-content-reject"]')).toHaveCount(0);
  await expect(page.locator("#response-content-verdict-status")).toContainText("저장 승인 거절과는 별도입니다.");
  await expect(page.locator("#response-content-verdict-status")).toContainText("이미 열린 저장 승인 카드는 그대로 유지되며 자동 취소되지 않습니다.");
  await expect(page.locator("#approval-preview")).toContainText("중간 섹션 핵심 결정은 승인 기반 저장을 유지하는 것입니다.");

  const originalApprovalPreview = (await page.locator("#approval-preview").textContent()) || "";

  await page.getByTestId("response-content-reject").click();

  await expect(page.locator("#notice-box")).toContainText("내용 거절을 기록했습니다. 저장 승인 거절과는 별도입니다.");
  await expect(page.locator("#response-content-verdict-state")).toContainText("내용 거절 기록됨");
  await expect(page.locator("#response-content-verdict-status")).toContainText("이 답변 내용을 거절로 기록했습니다.");
  await expect(page.locator("#response-content-verdict-status")).toContainText("이미 열린 저장 승인 카드는 그대로 유지되며 자동 취소되지 않습니다.");
  await expect(responseBox.getByTestId("response-content-reason-box")).toBeVisible();
  await expect(responseBox.getByTestId("response-content-reason-submit")).toBeDisabled();
  await expect(page.locator("#response-content-reason-status")).toContainText("비워 두면 메모 기록 버튼이 켜지지 않으며");
  await page.getByTestId("response-content-reason-input").fill(rejectNote);
  await expect(responseBox.getByTestId("response-content-reason-submit")).toBeEnabled();
  await page.getByTestId("response-content-reason-submit").click();
  await expect(page.locator("#notice-box")).toContainText("거절 메모를 기록했습니다. 내용 거절 판정은 그대로 유지됩니다.");
  await expect(page.getByTestId("response-content-reason-input")).toHaveValue(rejectNote);
  await expect(page.locator("#response-content-reason-status")).toContainText("기록된 거절 메모가 있습니다");
  await expect(page.locator("#response-quick-meta-text")).toContainText("내용 거절 기록됨");
  await expect(approvalBox).toBeVisible();
  await expect(page.getByTestId("approval-path-input")).toHaveValue(rejectedVerdictNotePath);
  await expect(page.locator("#approval-preview")).toHaveText(originalApprovalPreview);
  await expect(page.getByTestId("approve-button")).toBeEnabled();

  await page.getByTestId("approve-button").click();

  await expect(responseBox).toContainText("저장했습니다.");
  await expect
    .poll(async () => {
      const payload = await fetchSessionPayload(page, sessionId);
      return Array.isArray(payload.session?.pending_approvals) ? payload.session.pending_approvals.length : -1;
    })
    .toBe(0);
  await expect(approvalBox).toBeHidden();
  await expect(page.locator("#response-saved-path-row")).toBeVisible();
  await expect(page.locator("#response-saved-path")).toContainText("rejected-verdict-note.md");
  await expect(page.locator("#response-content-verdict-state")).toContainText("최신 내용 판정은 원문 저장 승인입니다.");
  await expect(responseBox.getByTestId("response-content-reason-box")).toBeHidden();
  await expect(page.getByTestId("response-content-reject")).toBeEnabled();
  await expect(page.locator("#response-quick-meta-text")).not.toContainText("내용 거절 기록됨");
  expect(fs.existsSync(rejectedVerdictNotePath)).toBeTruthy();
});

test("corrected-save first bridge path가 기록본 기준 승인 스냅샷으로 저장됩니다", async ({ page }) => {
  const correctedTextA = "수정본 A입니다.\n핵심만 남겼습니다.";
  const correctedTextB = "수정본 B입니다.\n다시 손봤습니다.";

  await prepareSession(page, "corrected-save");
  await page.getByTestId("source-path").fill(longFixturePath);
  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("response-box")).toContainText("중간 섹션 핵심 결정은 승인 기반 저장을 유지하는 것입니다.");
  await expect(page.getByTestId("response-correction-box")).toBeVisible();
  await expect(page.getByTestId("response-correction-save-request")).toBeVisible();
  await expect(page.getByTestId("response-correction-save-request")).toBeDisabled();
  await expect(page.locator("#response-correction-status")).toContainText("먼저 수정본 기록을 눌러야 저장 요청 버튼이 켜집니다.");
  await expect(page.locator("#response-correction-status")).toContainText("미기록 텍스트는 바로 승인 스냅샷이 되지 않습니다.");

  await page.getByTestId("response-correction-input").fill(correctedTextA);
  await expect(page.getByTestId("response-correction-submit")).toBeEnabled();
  await page.getByTestId("response-correction-submit").click();

  await expect(page.locator("#notice-box")).toContainText("수정본을 기록했습니다.");
  await expect(page.getByTestId("response-correction-save-request")).toBeEnabled();
  await expect(page.locator("#response-correction-state")).toContainText("기록된 수정본이 있습니다");
  await expect(page.locator("#response-correction-status")).toContainText("이미 기록된 수정본으로 새 승인 미리보기를 만듭니다.");

  await page.getByTestId("response-correction-save-request").click();

  await expect(page.locator("#notice-box")).toContainText("기록된 수정본 기준 저장 승인을 만들었습니다.");
  await expect(page.getByTestId("approval-box")).toBeVisible();
  await expect(page.locator("#approval-meta")).toContainText("저장 기준: 기록된 수정본 스냅샷");
  await expect(page.locator("#approval-meta")).toContainText("요청 시점에 고정되며");
  await expect(page.locator("#approval-meta")).toContainText("새 저장 요청을 다시 만들어야 합니다.");
  await expect(page.locator("#approval-meta")).not.toContainText("저장 기준: 원래 grounded brief 초안");
  await expect(page.locator("#approval-preview")).toContainText("수정본 A입니다.");
  await expect(page.getByTestId("response-box")).toContainText("현재 기록된 수정본 스냅샷");

  await page.getByTestId("response-correction-input").fill(correctedTextB);
  await expect(page.getByTestId("response-correction-save-request")).toBeEnabled();
  await expect(page.locator("#response-correction-state")).toContainText("입력창 변경이 아직 다시 기록되지 않았습니다.");
  await expect(page.locator("#response-correction-status")).toContainText("저장 요청 버튼은 직전 기록본으로만 동작합니다.");
  await expect(page.locator("#response-correction-status")).toContainText("이미 열린 저장 승인 카드도 이전 요청 시점 스냅샷으로 그대로 유지됩니다.");
  await expect(page.locator("#approval-preview")).toContainText("수정본 A입니다.");
  await expect(page.locator("#approval-preview")).not.toContainText("수정본 B입니다.");

  await page.getByTestId("approve-button").click();

  await expect(page.getByTestId("approval-box")).toBeHidden();
  await expect(page.getByTestId("response-box")).toContainText("승인 시점에 고정된 수정본");
  await expect(page.getByTestId("response-box")).toContainText("다시 저장 요청해 주세요.");
  await expect(page.locator("#response-saved-path-row")).toBeVisible();
  await expect(page.locator("#response-saved-path")).toContainText("long-summary-fixture-summary.md");
  expect(fs.existsSync(correctedBridgeNotePath)).toBeTruthy();
  expect(fs.readFileSync(correctedBridgeNotePath, "utf-8")).toBe(correctedTextA);
});

test("corrected-save 저장 뒤 늦게 내용 거절하고 다시 수정해도 saved snapshot과 latest state가 분리됩니다", async ({ page }) => {
  const correctedTextA = "수정본 A입니다.\n핵심만 남겼습니다.";
  const correctedTextB = "수정본 B입니다.\n다시 손봤습니다.";
  const rejectNote = "초기 수정본의 결론이 여전히 과장되어 있습니다.";

  await prepareSession(page, "corrected-long-history");
  await page.getByTestId("source-path").fill(longFixturePath);
  await page.getByTestId("submit-request").click();

  const responseBox = page.getByTestId("response-box");

  await page.getByTestId("response-correction-input").fill(correctedTextA);
  await page.getByTestId("response-correction-submit").click();
  await expect(page.locator("#notice-box")).toContainText("수정본을 기록했습니다.");

  await page.getByTestId("response-correction-save-request").click();
  await expect(page.getByTestId("approval-box")).toBeVisible();
  await expect(page.locator("#approval-meta")).toContainText("저장 기준: 기록된 수정본 스냅샷");
  await expect(page.locator("#approval-preview")).toContainText("수정본 A입니다.");

  await page.getByTestId("approve-button").click();

  await expect(responseBox).toContainText("승인 시점에 고정된 수정본");
  await expect(page.locator("#response-quick-meta-text")).toContainText("저장 기준 요청 시점 수정본 스냅샷");
  await expect(page.locator("#response-saved-path-row")).toBeVisible();
  await expect(page.locator("#response-content-verdict-state")).toContainText("최신 내용 판정은 기록된 수정본입니다.");
  await expect(page.locator("#response-correction-state")).toContainText("기록된 수정본이 있습니다");
  expect(fs.existsSync(correctedBridgeNotePath)).toBeTruthy();
  expect(fs.readFileSync(correctedBridgeNotePath, "utf-8")).toBe(correctedTextA);

  await page.getByTestId("response-content-reject").click();

  await expect(responseBox).toContainText("승인 시점에 고정된 수정본");
  await expect(page.locator("#notice-box")).toContainText("이미 저장된 노트는 그대로 유지되며 최신 내용 판정만 바뀝니다.");
  await expect(page.locator("#response-quick-meta-text")).toContainText("저장 기준 요청 시점 수정본 스냅샷");
  await expect(page.locator("#response-quick-meta-text")).not.toContainText("내용 거절 기록됨");
  await expect(page.locator("#response-content-verdict-state")).toContainText("내용 거절 기록됨");
  await expect(page.locator("#response-content-verdict-status")).toContainText("이미 저장된 노트와 경로는 그대로 남고, 이번 내용 거절은 최신 판정만 바꿉니다.");
  await expect(page.getByTestId("response-content-reason-box")).toBeVisible();
  expect(fs.readFileSync(correctedBridgeNotePath, "utf-8")).toBe(correctedTextA);

  await page.getByTestId("response-content-reason-input").fill(rejectNote);
  await page.getByTestId("response-content-reason-submit").click();
  await expect(page.locator("#notice-box")).toContainText("거절 메모를 기록했습니다. 내용 거절 판정은 그대로 유지됩니다.");
  await expect(page.locator("#response-content-reason-status")).toContainText("기록된 거절 메모가 있습니다");

  await page.getByTestId("response-correction-input").fill(correctedTextB);
  await page.getByTestId("response-correction-submit").click();

  await expect(page.locator("#notice-box")).toContainText("수정본을 기록했습니다.");
  await expect(responseBox).toContainText("승인 시점에 고정된 수정본");
  await expect(page.locator("#response-quick-meta-text")).toContainText("저장 기준 요청 시점 수정본 스냅샷");
  await expect(page.locator("#response-quick-meta-text")).not.toContainText("내용 거절 기록됨");
  await expect(page.locator("#response-content-verdict-state")).toContainText("최신 내용 판정은 기록된 수정본입니다.");
  await expect(page.getByTestId("response-content-reason-box")).toBeHidden();
  await expect(page.getByTestId("response-correction-input")).toHaveValue(correctedTextB);
  await expect(page.locator("#response-correction-state")).toContainText("기록된 수정본이 있습니다");
  await expect(page.locator("#response-correction-status")).toContainText("이미 기록된 수정본으로 새 승인 미리보기를 만듭니다.");
  await expect(page.getByTestId("response-correction-save-request")).toBeEnabled();
  await expect(page.locator("#response-saved-path-row")).toBeVisible();
  expect(fs.readFileSync(correctedBridgeNotePath, "utf-8")).toBe(correctedTextA);
});

test("candidate confirmation path는 save support와 분리되어 기록되고 later correction으로 current state에서 사라집니다", async ({ page }) => {
  const correctedTextA = "수정 방향 A입니다.\n핵심만 남겼습니다.";
  const correctedTextB = "수정 방향 B입니다.\n다시 손봤습니다.";

  const sessionId = await prepareSession(page, "candidate-confirmation");
  await page.getByTestId("source-path").fill(longFixturePath);
  await page.getByTestId("submit-request").click();

  const responseBox = page.getByTestId("response-box");
  const approvalBox = page.getByTestId("approval-box");
  const confirmationBox = page.getByTestId("response-candidate-confirmation-box");
  const confirmationButton = page.getByTestId("response-candidate-confirmation-submit");
  const reviewQueueBox = page.getByTestId("review-queue-box");

  await expect(responseBox).toContainText(middleSignal);
  await expect(confirmationBox).toBeHidden();
  await expect(reviewQueueBox).toBeHidden();

  await page.getByTestId("response-correction-input").fill(correctedTextA);
  await page.getByTestId("response-correction-submit").click();

  await expect(page.locator("#notice-box")).toContainText("수정본을 기록했습니다.");
  await expect(confirmationBox).toBeVisible();
  await expect(confirmationButton).toBeEnabled();
  await expect(page.locator("#response-candidate-confirmation-status")).toContainText("positive reuse confirmation만 남깁니다.");
  await expect(page.locator("#response-candidate-confirmation-status")).toContainText("저장 승인, 내용 거절, 거절 메모, 피드백과는 별도입니다.");

  await expect
    .poll(async () => {
      const payload = await fetchSessionPayload(page, sessionId);
      const message = findLatestCandidateSourceMessage(payload.session?.messages);
      return Array.isArray(message?.session_local_candidate?.supporting_signal_refs)
        ? message.session_local_candidate.supporting_signal_refs.length
        : 0;
    })
    .toBe(1);

  let sessionPayload = await fetchSessionPayload(page, sessionId);
  let sourceMessage = findLatestCandidateSourceMessage(sessionPayload.session?.messages);
  expect(sourceMessage).toBeTruthy();
  const sourceMessageId = sourceMessage.message_id;
  expect(sourceMessage.candidate_confirmation_record).toBeUndefined();
  expect(sourceMessage.session_local_candidate.supporting_signal_refs).toEqual([
    {
      signal_name: "session_local_memory_signal.content_signal",
      relationship: "primary_basis",
    },
  ]);

  await page.getByTestId("response-correction-save-request").click();

  await expect(approvalBox).toBeVisible();
  await expect(confirmationBox).toBeVisible();
  await expect(approvalBox.locator('[data-testid="response-candidate-confirmation-submit"]')).toHaveCount(0);
  await expect(page.locator("#response-candidate-confirmation-status")).toContainText("이미 열린 저장 승인 카드와도 섞이지 않습니다.");

  await page.getByTestId("approve-button").click();

  await expect(approvalBox).toBeHidden();
  await expect(responseBox).toContainText("승인 시점에 고정된 수정본");
  await expect(page.locator("#response-quick-meta-text")).toContainText("저장 기준 요청 시점 수정본 스냅샷");

  await expect
    .poll(async () => {
      const payload = await fetchSessionPayload(page, sessionId);
      const message = findMessageById(payload.session?.messages, sourceMessageId);
      return Array.isArray(message?.session_local_candidate?.supporting_signal_refs)
        ? message.session_local_candidate.supporting_signal_refs.length
        : 0;
    })
    .toBe(2);

  sessionPayload = await fetchSessionPayload(page, sessionId);
  sourceMessage = findMessageById(sessionPayload.session?.messages, sourceMessageId);
  expect(sourceMessage).toBeTruthy();
  expect(sourceMessage.candidate_confirmation_record).toBeUndefined();
  expect(sourceMessage.session_local_candidate.supporting_signal_refs).toEqual([
    {
      signal_name: "session_local_memory_signal.content_signal",
      relationship: "primary_basis",
    },
    {
      signal_name: "session_local_memory_signal.save_signal",
      relationship: "supporting_evidence",
    },
  ]);

  await expect(confirmationButton).toBeEnabled();
  await confirmationButton.click();

  await expect(page.locator("#notice-box")).toContainText("현재 수정 방향을 나중에도 다시 써도 된다는 확인을 기록했습니다. 저장 승인과는 별도입니다.");
  await expect(page.locator("#response-candidate-confirmation-state")).toContainText("재사용 확인 기록됨");
  await expect(confirmationButton).toBeDisabled();
  await expect(page.locator("#response-candidate-confirmation-status")).toContainText("positive reuse confirmation만 남겼습니다.");
  await expect(page.locator("#response-candidate-confirmation-status")).toContainText("저장 승인, 내용 거절, 거절 메모와는 별도입니다.");
  await expect(reviewQueueBox).toBeVisible();
  await expect(reviewQueueBox).toContainText("검토 후보");
  await expect(reviewQueueBox).toContainText("현재 후보는 검토 수락만 기록할 수 있습니다. 아직 적용, 편집, 거절은 열지 않았습니다.");
  await expect(reviewQueueBox).toContainText("explicit rewrite correction recorded for this grounded brief");
  await expect(reviewQueueBox).toContainText("기준 명시 확인");
  await expect(reviewQueueBox).toContainText("상태 검토 대기");
  const reviewAcceptButton = reviewQueueBox.getByTestId("review-queue-accept");
  await expect(reviewAcceptButton).toHaveCount(1);
  await expect(reviewAcceptButton).toHaveText("검토 수락");
  await reviewAcceptButton.click();

  await expect(page.locator("#notice-box")).toContainText("검토 후보를 수락했습니다. 아직 적용되지는 않았습니다.");
  await expect(reviewQueueBox).toBeHidden();

  sessionPayload = await fetchSessionPayload(page, sessionId);
  sourceMessage = findMessageById(sessionPayload.session?.messages, sourceMessageId);
  expect(sourceMessage.candidate_confirmation_record.confirmation_label).toBe("explicit_reuse_confirmation");
  expect(sourceMessage.candidate_confirmation_record.candidate_id).toBe(sourceMessage.session_local_candidate.candidate_id);
  expect(sourceMessage.session_local_candidate.supporting_signal_refs).toEqual([
    {
      signal_name: "session_local_memory_signal.content_signal",
      relationship: "primary_basis",
    },
    {
      signal_name: "session_local_memory_signal.save_signal",
      relationship: "supporting_evidence",
    },
  ]);
  expect("has_explicit_confirmation" in sourceMessage.session_local_candidate).toBe(false);
  expect("promotion_basis" in sourceMessage.session_local_candidate).toBe(false);
  expect("promotion_eligibility" in sourceMessage.session_local_candidate).toBe(false);
  expect(sourceMessage.durable_candidate.candidate_id).toBe(sourceMessage.session_local_candidate.candidate_id);
  expect(sourceMessage.durable_candidate.candidate_scope).toBe("durable_candidate");
  expect(sourceMessage.durable_candidate.has_explicit_confirmation).toBe(true);
  expect(sourceMessage.durable_candidate.promotion_basis).toBe("explicit_confirmation");
  expect(sourceMessage.durable_candidate.promotion_eligibility).toBe("eligible_for_review");
  expect(sourceMessage.durable_candidate.supporting_confirmation_refs).toEqual([
    {
      artifact_id: sourceMessage.artifact_id,
      source_message_id: sourceMessageId,
      candidate_id: sourceMessage.session_local_candidate.candidate_id,
      candidate_updated_at: sourceMessage.session_local_candidate.updated_at,
      confirmation_label: "explicit_reuse_confirmation",
      recorded_at: sourceMessage.candidate_confirmation_record.recorded_at,
    },
  ]);
  expect(sourceMessage.candidate_review_record).toEqual({
    candidate_id: sourceMessage.session_local_candidate.candidate_id,
    candidate_updated_at: sourceMessage.session_local_candidate.updated_at,
    artifact_id: sourceMessage.artifact_id,
    source_message_id: sourceMessageId,
    review_scope: "source_message_candidate_review",
    review_action: "accept",
    review_status: "accepted",
    recorded_at: sourceMessage.candidate_review_record.recorded_at,
  });
  expect(sessionPayload.session.review_queue_items).toEqual([]);

  await page.getByTestId("response-correction-input").fill(correctedTextB);
  await page.getByTestId("response-correction-submit").click();

  await expect(page.locator("#notice-box")).toContainText("수정본을 기록했습니다.");
  await expect(page.locator("#response-candidate-confirmation-state")).toContainText("현재 수정 방향 재사용 확인은 아직 없습니다.");
  await expect(confirmationButton).toBeEnabled();
  await expect(reviewQueueBox).toBeHidden();

  sessionPayload = await fetchSessionPayload(page, sessionId);
  sourceMessage = findMessageById(sessionPayload.session?.messages, sourceMessageId);
  expect(sourceMessage.candidate_review_record).toBeUndefined();
  expect(sourceMessage.candidate_confirmation_record).toBeUndefined();
  expect(sourceMessage.durable_candidate).toBeUndefined();
});

test("same-session recurrence aggregate는 separate blocked trigger surface로 렌더링됩니다", async ({ page }, testInfo) => {
  testInfo.setTimeout(60_000);
  const correctedText = "수정 방향 A입니다.\n핵심만 남겼습니다.";
  const sessionId = await prepareSession(page, "aggregate-trigger");
  const reviewQueueBox = page.getByTestId("review-queue-box");
  const aggregateTriggerBox = page.getByTestId("aggregate-trigger-box");

  await page.getByTestId("source-path").fill(shortFixturePath);
  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("response-box")).toContainText(middleSignal);
  await expect(reviewQueueBox).toBeHidden();
  await expect(aggregateTriggerBox).toBeHidden();

  await page.getByTestId("response-correction-input").fill(correctedText);
  await page.getByTestId("response-correction-submit").click();
  await expect(page.locator("#notice-box")).toContainText("수정본을 기록했습니다.");
  await expect(page.getByTestId("response-candidate-confirmation-box")).toBeVisible();
  await page.getByTestId("response-candidate-confirmation-submit").click();

  await expect(page.locator("#notice-box")).toContainText("현재 수정 방향을 나중에도 다시 써도 된다는 확인을 기록했습니다. 저장 승인과는 별도입니다.");
  await expect(reviewQueueBox).toBeVisible();
  await expect(reviewQueueBox).toContainText("검토 후보");
  await expect(aggregateTriggerBox).toBeHidden();

  await page.getByTestId("source-path").fill(shortFixturePath);
  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("response-box")).toContainText(middleSignal);
  await page.getByTestId("response-correction-input").fill(correctedText);
  await page.getByTestId("response-correction-submit").click();

  await expect(page.locator("#notice-box")).toContainText("수정본을 기록했습니다.");
  await expect(aggregateTriggerBox).toBeVisible();
  await expect(aggregateTriggerBox).toContainText("검토 메모 적용 후보");
  await expect(aggregateTriggerBox).toContainText("반복 교정 묶음");
  await expect(aggregateTriggerBox).toContainText("capability unblocked_all_required");
  await expect(aggregateTriggerBox).toContainText("audit contract_only_not_emitted");
  await expect(aggregateTriggerBox).toContainText("계획 타깃 eligible_for_reviewed_memory_draft_planning_only");
  await expect(aggregateTriggerBox).toContainText("검토 메모 적용을 시작할 수 있습니다. 사유를 입력한 뒤 시작 버튼을 누르세요.");

  const noteInput = aggregateTriggerBox.getByTestId("aggregate-trigger-note");
  await expect(noteInput).toBeVisible();

  const startButton = aggregateTriggerBox.getByTestId("aggregate-trigger-start");
  await expect(startButton).toBeVisible();
  await expect(startButton).toBeDisabled();

  await noteInput.fill("반복 교정 패턴을 적용합니다.");
  await expect(startButton).toBeEnabled();

  await startButton.click();
  await expect(page.locator("#notice-box")).toContainText("transition record가 발행되었습니다.");

  await expect(reviewQueueBox).toBeVisible();
  await expect(reviewQueueBox).toContainText("검토 수락");

  const emittedPayload = await fetchSessionPayload(page, sessionId);
  expect(emittedPayload.session.recurrence_aggregate_candidates).toHaveLength(1);
  const emittedAggregate = emittedPayload.session.recurrence_aggregate_candidates[0];
  expect(emittedAggregate.reviewed_memory_transition_record).toBeDefined();
  expect(emittedAggregate.reviewed_memory_transition_record.transition_record_version).toBe("first_reviewed_memory_transition_record_v1");
  expect(emittedAggregate.reviewed_memory_transition_record.transition_action).toBe("future_reviewed_memory_apply");
  expect(emittedAggregate.reviewed_memory_transition_record.operator_reason_or_note).toBe("반복 교정 패턴을 적용합니다.");
  expect(emittedAggregate.reviewed_memory_transition_record.record_stage).toBe("emitted_record_only_not_applied");
  expect(emittedAggregate.reviewed_memory_transition_record.canonical_transition_id).toBeTruthy();
  expect(emittedAggregate.reviewed_memory_transition_record.emitted_at).toBeTruthy();

  const applyButton = aggregateTriggerBox.getByTestId("aggregate-trigger-apply");
  await expect(applyButton).toBeVisible();
  await expect(applyButton).toBeEnabled();
  await applyButton.click();
  await expect(page.locator("#notice-box")).toContainText("검토 메모 적용이 실행되었습니다.");

  const appliedPayload = await fetchSessionPayload(page, sessionId);
  expect(appliedPayload.session.recurrence_aggregate_candidates).toHaveLength(1);
  const appliedAggregate = appliedPayload.session.recurrence_aggregate_candidates[0];
  expect(appliedAggregate.reviewed_memory_transition_record.record_stage).toBe("applied_pending_result");
  expect(appliedAggregate.reviewed_memory_transition_record.applied_at).toBeTruthy();
  expect(appliedAggregate.reviewed_memory_transition_record.canonical_transition_id).toBe(
    emittedAggregate.reviewed_memory_transition_record.canonical_transition_id
  );

  const confirmResultButton = aggregateTriggerBox.getByTestId("aggregate-trigger-confirm-result");
  await expect(confirmResultButton).toBeVisible();
  await expect(confirmResultButton).toBeEnabled();
  await confirmResultButton.click();
  await expect(page.locator("#notice-box")).toContainText("검토 메모 적용 결과가 확정되었습니다.");

  const resultPayload = await fetchSessionPayload(page, sessionId);
  expect(resultPayload.session.recurrence_aggregate_candidates).toHaveLength(1);
  const resultAggregate = resultPayload.session.recurrence_aggregate_candidates[0];
  expect(resultAggregate.reviewed_memory_transition_record.record_stage).toBe("applied_with_result");
  expect(resultAggregate.reviewed_memory_transition_record.result_at).toBeTruthy();
  expect(resultAggregate.reviewed_memory_transition_record.apply_result).toBeDefined();
  expect(resultAggregate.reviewed_memory_transition_record.apply_result.result_version).toBe("first_reviewed_memory_apply_result_v1");
  expect(resultAggregate.reviewed_memory_transition_record.apply_result.applied_effect_kind).toBe("reviewed_memory_correction_pattern");
  expect(resultAggregate.reviewed_memory_transition_record.apply_result.result_stage).toBe("effect_active");
  expect(resultAggregate.reviewed_memory_transition_record.canonical_transition_id).toBe(
    emittedAggregate.reviewed_memory_transition_record.canonical_transition_id
  );

  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-result")).toBeVisible();
  await expect(aggregateTriggerBox).toContainText("검토 메모 적용 효과가 활성화되었습니다.");

  await page.getByTestId("source-path").fill(shortFixturePath);
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-box")).toContainText("[검토 메모 활성]");
  await expect(page.getByTestId("response-box")).toContainText("반복 교정 패턴을 적용합니다.");

  const stopButton = aggregateTriggerBox.getByTestId("aggregate-trigger-stop");
  await expect(stopButton).toBeVisible();
  await expect(stopButton).toBeEnabled();
  await stopButton.click();
  await expect(page.locator("#notice-box")).toContainText("검토 메모 적용이 중단되었습니다.");

  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-stopped")).toBeVisible();
  await expect(aggregateTriggerBox).toContainText("검토 메모 적용이 중단되었습니다. 이후 응답에 교정 패턴이 반영되지 않습니다.");

  const stoppedPayload = await fetchSessionPayload(page, sessionId);
  const stoppedAggregate = stoppedPayload.session.recurrence_aggregate_candidates[0];
  expect(stoppedAggregate.reviewed_memory_transition_record.record_stage).toBe("stopped");
  expect(stoppedAggregate.reviewed_memory_transition_record.stopped_at).toBeTruthy();
  expect(stoppedAggregate.reviewed_memory_transition_record.apply_result.result_stage).toBe("effect_stopped");

  await page.getByTestId("source-path").fill(shortFixturePath);
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-box")).not.toContainText("[검토 메모 활성]");

  const reverseButton = aggregateTriggerBox.getByTestId("aggregate-trigger-reverse");
  await expect(reverseButton).toBeVisible();
  await expect(reverseButton).toBeEnabled();
  await reverseButton.click();
  await expect(page.locator("#notice-box")).toContainText("검토 메모 적용이 되돌려졌습니다.");

  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-reversed")).toBeVisible();
  await expect(aggregateTriggerBox).toContainText("검토 메모 적용이 되돌려졌습니다. 적용 효과가 완전히 철회되었습니다.");

  const reversedPayload = await fetchSessionPayload(page, sessionId);
  const reversedAggregate = reversedPayload.session.recurrence_aggregate_candidates[0];
  expect(reversedAggregate.reviewed_memory_transition_record.record_stage).toBe("reversed");
  expect(reversedAggregate.reviewed_memory_transition_record.reversed_at).toBeTruthy();
  expect(reversedAggregate.reviewed_memory_transition_record.apply_result.result_stage).toBe("effect_reversed");
  expect(reversedAggregate.reviewed_memory_transition_record.canonical_transition_id).toBe(
    emittedAggregate.reviewed_memory_transition_record.canonical_transition_id
  );

  const conflictCheckButton = aggregateTriggerBox.getByTestId("aggregate-trigger-conflict-check");
  await expect(conflictCheckButton).toBeVisible();
  await expect(conflictCheckButton).toBeEnabled();
  await conflictCheckButton.click();
  await expect(page.locator("#notice-box")).toContainText("충돌 확인이 완료되었습니다.");

  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-conflict-checked")).toBeVisible();
  await expect(aggregateTriggerBox).toContainText("충돌 확인이 완료되었습니다. 현재 aggregate 범위의 충돌 상태가 기록되었습니다.");

  const conflictPayload = await fetchSessionPayload(page, sessionId);
  const conflictAggregate = conflictPayload.session.recurrence_aggregate_candidates[0];
  expect(conflictAggregate.reviewed_memory_conflict_visibility_record).toBeDefined();
  expect(conflictAggregate.reviewed_memory_conflict_visibility_record.transition_action).toBe("future_reviewed_memory_conflict_visibility");
  expect(conflictAggregate.reviewed_memory_conflict_visibility_record.record_stage).toBe("conflict_visibility_checked");
  expect(conflictAggregate.reviewed_memory_conflict_visibility_record.conflict_visibility_stage).toBe("conflict_visibility_checked");
  expect(conflictAggregate.reviewed_memory_conflict_visibility_record.canonical_transition_id).toBeTruthy();
  expect(conflictAggregate.reviewed_memory_conflict_visibility_record.checked_at).toBeTruthy();
  expect(conflictAggregate.reviewed_memory_conflict_visibility_record.source_apply_transition_ref).toBe(
    emittedAggregate.reviewed_memory_transition_record.canonical_transition_id
  );
  expect(typeof conflictAggregate.reviewed_memory_conflict_visibility_record.conflict_entry_count).toBe("number");
  expect(Array.isArray(conflictAggregate.reviewed_memory_conflict_visibility_record.conflict_entries)).toBe(true);

  expect(conflictAggregate.reviewed_memory_transition_record.record_stage).toBe("reversed");
  expect(conflictAggregate.reviewed_memory_transition_record.canonical_transition_id).toBe(
    emittedAggregate.reviewed_memory_transition_record.canonical_transition_id
  );
});

test("스트리밍 중 취소 버튼이 동작합니다", async ({ page }) => {
  await prepareSession(page, "cancel");
  await page.getByTestId("source-path").fill(longFixturePath);
  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("cancel-request")).toBeVisible();
  await page.getByTestId("cancel-request").click();

  await expect(page.locator("#notice-box")).toContainText("요청을 취소했습니다.");
});

test("일반 채팅 응답에는 source-type label이 붙지 않습니다", async ({ page }) => {
  await prepareSession(page, "general-chat");
  await page.locator('input[name="request_mode"][value="chat"]').check();
  await page.locator("#user-text").fill("안녕하세요");
  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("response-box")).not.toBeEmpty();
  const quickMetaText = await page.locator("#response-quick-meta-text").textContent();
  expect(quickMetaText).not.toContain("문서 요약");
  expect(quickMetaText).not.toContain("선택 결과 요약");
  const transcriptMeta = page.locator('#transcript [data-testid="transcript-meta"]').last();
  if (await transcriptMeta.count() > 0) {
    const metaText = await transcriptMeta.textContent();
    expect(metaText).not.toContain("문서 요약");
    expect(metaText).not.toContain("선택 결과 요약");
  }
});

test("claim-coverage panel은 status tag와 행동 힌트를 올바르게 렌더링합니다", async ({ page }) => {
  await prepareSession(page, "claim-coverage");

  await page.evaluate(() => {
    // @ts-ignore — renderClaimCoverage is defined in the page scope
    renderClaimCoverage([
      { slot: "출생일", status_label: "교차 확인", value: "1990년 3월 15일", support_count: 2 },
      { slot: "소속", status_label: "단일 출처", value: "A 대학교", support_count: 1 },
      { slot: "수상 이력", status_label: "미확인", value: "", support_count: 0 },
    ]);
  });

  const box = page.getByTestId("claim-coverage-box");
  await expect(box).toBeVisible();

  const text = page.locator("#claim-coverage-text");
  await expect(text).toContainText("[교차 확인] 출생일");
  await expect(text).toContainText("[단일 출처] 소속");
  await expect(text).toContainText("[미확인] 수상 이력");
  await expect(text).toContainText("1개 출처만 확인됨. 교차 검증이 권장됩니다.");
  await expect(text).toContainText("추가 출처가 필요합니다.");

  const hint = page.locator("#claim-coverage-hint");
  await expect(hint).toContainText("교차 확인은 여러 출처 합의");
  await expect(hint).toContainText("단일 출처는 신뢰 가능한 1개 출처 기준");
  await expect(hint).toContainText("미확인은 추가 조사 필요 상태입니다");
});

test("web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다", async ({ page }) => {
  await prepareSession(page, "search-history-badges");

  await page.evaluate(() => {
    // @ts-ignore — renderSearchHistory is defined in the page scope
    renderSearchHistory([
      {
        query: "대통령 출생일",
        answer_mode: "entity_card",
        verification_label: "공식+기사 교차 확인",
        source_roles: ["공식 기반", "보조 기사"],
        result_count: 5,
        page_count: 3,
        created_at: new Date().toISOString(),
      },
      {
        query: "최근 경제 동향",
        answer_mode: "latest_update",
        verification_label: "설명형 단일 출처",
        source_roles: ["설명형 출처"],
        result_count: 3,
        page_count: 1,
        created_at: new Date().toISOString(),
      },
      {
        query: "일반 검색어",
        answer_mode: "general",
        verification_label: "보조 커뮤니티 참고",
        source_roles: ["보조 커뮤니티"],
        result_count: 2,
        page_count: 0,
        created_at: new Date().toISOString(),
      },
      {
        query: "테스트게임",
        answer_mode: "entity_card",
        verification_label: "설명형 단일 출처",
        source_roles: ["백과 기반"],
        result_count: 2,
        page_count: 0,
        created_at: new Date().toISOString(),
      },
    ]);
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();

  const cards = historyBox.locator(".history-item");
  await expect(cards).toHaveCount(4);

  // Card 1: entity_card — answer-mode badge, strong verification, high+medium source roles
  const card1 = cards.nth(0);
  const card1Badges = card1.locator(".history-badge-row");
  await expect(card1Badges.locator(".answer-mode-badge")).toHaveText("설명 카드");
  await expect(card1Badges.locator(".verification-badge")).toHaveText("검증 강");
  await expect(card1Badges.locator(".verification-badge")).toHaveClass(/ver-strong/);
  const card1Roles = card1Badges.locator(".source-role-badge");
  await expect(card1Roles).toHaveCount(2);
  await expect(card1Roles.nth(0)).toHaveText("공식 기반(높음)");
  await expect(card1Roles.nth(0)).toHaveClass(/trust-high/);
  await expect(card1Roles.nth(1)).toHaveText("보조 기사(보통)");
  await expect(card1Roles.nth(1)).toHaveClass(/trust-medium/);

  // Card 2: latest_update — answer-mode badge, medium verification, medium source role
  const card2 = cards.nth(1);
  const card2Badges = card2.locator(".history-badge-row");
  await expect(card2Badges.locator(".answer-mode-badge")).toHaveText("최신 확인");
  await expect(card2Badges.locator(".verification-badge")).toHaveText("검증 중");
  await expect(card2Badges.locator(".verification-badge")).toHaveClass(/ver-medium/);
  const card2Roles = card2Badges.locator(".source-role-badge");
  await expect(card2Roles).toHaveCount(1);
  await expect(card2Roles.nth(0)).toHaveText("설명형 출처(보통)");
  await expect(card2Roles.nth(0)).toHaveClass(/trust-medium/);

  // Card 3: general — no answer-mode badge (not investigation), weak verification, low source role
  const card3 = cards.nth(2);
  const card3Badges = card3.locator(".history-badge-row");
  await expect(card3Badges.locator(".answer-mode-badge")).toHaveCount(0);
  await expect(card3Badges.locator(".verification-badge")).toHaveText("검증 약");
  await expect(card3Badges.locator(".verification-badge")).toHaveClass(/ver-weak/);
  const card3Roles = card3Badges.locator(".source-role-badge");
  await expect(card3Roles).toHaveCount(1);
  await expect(card3Roles.nth(0)).toHaveText("보조 커뮤니티(낮음)");
  await expect(card3Roles.nth(0)).toHaveClass(/trust-low/);

  // Card 4: entity_card with zero-strong-slot — answer-mode badge, medium (not strong) verification, high source role
  const card4 = cards.nth(3);
  const card4Badges = card4.locator(".history-badge-row");
  await expect(card4Badges.locator(".answer-mode-badge")).toHaveText("설명 카드");
  await expect(card4Badges.locator(".verification-badge")).toHaveText("검증 중");
  await expect(card4Badges.locator(".verification-badge")).toHaveClass(/ver-medium/);
  const card4Roles = card4Badges.locator(".source-role-badge");
  await expect(card4Roles).toHaveCount(1);
  await expect(card4Roles.nth(0)).toHaveText("백과 기반(높음)");
  await expect(card4Roles.nth(0)).toHaveClass(/trust-high/);
});

test("history-card 다시 불러오기 클릭 후 response origin badge와 answer-mode badge가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload");

  // Pre-seed a web search record on disk so the server can load it
  const recordId = `websearch-e2etest${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 1,
    page_count: 0,
    results: [
      {
        title: "붉은사막 - 나무위키",
        url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 붉은사막",
    response_origin: {},
    claim_coverage: [],
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card in the browser with the pre-seeded record_id
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "붉은사막",
          answer_mode: "entity_card",
          verification_label: "설명형 단일 출처",
          source_roles: ["백과 기반"],
          result_count: 1,
          page_count: 0,
          created_at: record.created_at,
          record_path: recordPath,
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  const reloadButton = historyBox.locator(".history-item-actions button.secondary").first();
  await expect(reloadButton).toHaveText("다시 불러오기");

  // Click "다시 불러오기" — triggers loadWebSearchRecord(recordId)
  await reloadButton.click();

  // Wait for the response to render with a WEB badge
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);

  // Answer-mode badge should show "설명 카드" for entity_card
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");

  // Origin detail should contain verification label and source role info
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 단일 출처");
  await expect(originDetail).toContainText("백과 기반");

  // Clean up the pre-seeded record
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});
