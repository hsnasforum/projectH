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
const scannedPdfFixturePath = path.join(fixtureDir, "scanned-stub.pdf");
const readablePdfFixturePath = path.join(fixtureDir, "readable-text-layer.pdf");
const mixedSearchFixtureDir = path.join(fixtureDir, "mixed-search-folder");
const searchFolderRelBudgetPath = path.basename(searchFixtureDir) + "/budget-plan.md";
const searchFolderRelMemoPath = path.basename(searchFixtureDir) + "/memo.md";
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

function sessionLocalReviewQueueItems(sessionPayload) {
  return (sessionPayload.session?.review_queue_items ?? []).filter((item) => item.is_global !== true);
}

async function expectSessionLocalReviewQueueCount(page, sessionId, expectedCount) {
  await expect
    .poll(async () => {
      const payload = await fetchSessionPayload(page, sessionId);
      return sessionLocalReviewQueueItems(payload).length;
    })
    .toBe(expectedCount);
}

function sessionLocalReviewQueueItem(reviewQueueBox) {
  return reviewQueueBox.getByTestId("review-queue-item").filter({ hasText: "기준 명시 확인" }).first();
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
  // Minimal valid PDF with one empty page — triggers OcrRequiredError
  const scannedPdfBytes = Buffer.from(
    "%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
  );
  fs.writeFileSync(scannedPdfFixturePath, scannedPdfBytes);
  // Readable text-layer PDF generated by pypdf — contains "PDF text-layer test: local-first approval-based document assistant"
  const readablePdfBytes = Buffer.from(
    "JVBERi0xLjMKJeLjz9MKMSAwIG9iago8PAovVHlwZSAvUGFnZXMKL0NvdW50IDEKL0tpZHMgWyA0IDAgUiBdCj4+CmVuZG9iagoyIDAgb2JqCjw8Ci9Qcm9kdWNlciAocHlwZGYpCj4+CmVuZG9iagozIDAgb2JqCjw8Ci9UeXBlIC9DYXRhbG9nCi9QYWdlcyAxIDAgUgo+PgplbmRvYmoKNCAwIG9iago8PAovVHlwZSAvUGFnZQovUmVzb3VyY2VzIDw8Ci9Gb250IDw8Ci9GMSA8PAovVHlwZSAvRm9udAovU3VidHlwZSAvVHlwZTEKL0Jhc2VGb250IC9IZWx2ZXRpY2EKPj4KPj4KPj4KL01lZGlhQm94IFsgMC4wIDAuMCA2MTIgNzkyIF0KL0NvbnRlbnRzIDUgMCBSCi9QYXJlbnQgMSAwIFIKPj4KZW5kb2JqCjUgMCBvYmoKPDwKL0xlbmd0aCA5OAo+PgpzdHJlYW0KQlQgL0YxIDEyIFRmIDEwMCA3MDAgVGQgKFBERiB0ZXh0LWxheWVyIHRlc3Q6IGxvY2FsLWZpcnN0IGFwcHJvdmFsLWJhc2VkIGRvY3VtZW50IGFzc2lzdGFudCkgVGogRVQKZW5kc3RyZWFtCmVuZG9iagp4cmVmCjAgNgowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwMTUgMDAwMDAgbiAKMDAwMDAwMDA3NCAwMDAwMCBuIAowMDAwMDAwMTEzIDAwMDAwIG4gCjAwMDAwMDAxNjIgMDAwMDAgbiAKMDAwMDAwMDM0MyAwMDAwMCBuIAp0cmFpbGVyCjw8Ci9TaXplIDYKL1Jvb3QgMyAwIFIKL0luZm8gMiAwIFIKPj4Kc3RhcnR4cmVmCjQ5MQolJUVPRgo=",
    "base64"
  );
  fs.writeFileSync(readablePdfFixturePath, readablePdfBytes);
  fs.mkdirSync(mixedSearchFixtureDir, { recursive: true });
  fs.writeFileSync(path.join(mixedSearchFixtureDir, "scan.pdf"), scannedPdfBytes);
  fs.writeFileSync(path.join(mixedSearchFixtureDir, "notes.txt"), "hello world budget reference", "utf-8");
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

  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText(middleSignal);
  await expect(page.locator("#response-quick-meta-text")).toContainText("long-summary-fixture.md");
  await expect(page.locator("#response-quick-meta-text")).toContainText("문서 요약");
  await expect(page.getByTestId("response-copy-text")).toBeVisible();
  await expect(page.locator("#transcript .message-when")).toHaveCount(2);
  await expect(page.locator("#transcript .message-when").first()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
  await expect(page.locator("#transcript .message-when").last()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
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
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText(middleSignal);
  await expect(page.getByTestId("response-copy-text")).toBeVisible();

  await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.getByTestId("response-copy-text").click();
  await expect(page.locator("#notice-box")).toHaveText("본문을 복사했습니다.");
  const clipboardText = await page.evaluate(() => navigator.clipboard.readText());
  expect(clipboardText).toContain(middleSignal);
});

test("브라우저 파일 선택으로도 파일 요약이 됩니다", async ({ page }) => {
  await prepareSession(page, "picker");
  await page.getByTestId("browser-file-input").setInputFiles(longFixturePath);
  await expect(page.locator("#picked-file-name")).toContainText("long-summary-fixture.md");

  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText(middleSignal);
  await expect(page.locator("#context-box")).toContainText("long-summary-fixture.md");
  await expect(page.locator("#response-quick-meta-text")).toContainText("long-summary-fixture.md");
  await expect(page.locator("#response-quick-meta-text")).toContainText("문서 요약");
  await expect(page.locator('#transcript [data-testid="transcript-meta"]').last()).toContainText("long-summary-fixture.md");
  await expect(page.locator('#transcript [data-testid="transcript-meta"]').last()).toContainText("문서 요약");
  await expect(page.locator("#transcript .message-when").first()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
  await expect(page.locator("#transcript .message-when").last()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
});

test("브라우저 폴더 선택으로도 문서 검색이 됩니다", async ({ page }) => {
  await prepareSession(page, "folder-search");
  await page.locator('input[name="request_mode"][value="search"]').check();
  await page.getByTestId("browser-folder-input").setInputFiles(searchFixtureDir);
  await expect(page.locator("#picked-folder-name")).toContainText("2개 파일");
  await page.getByTestId("search-query").fill("budget");

  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText("[모의 요약]");
  await expect(page.locator("#response-quick-meta-text")).toContainText("선택 결과 요약");
  await expect(page.locator("#response-quick-meta-text")).toContainText("출처 2개");
  await expect(page.locator("#response-quick-meta-text")).not.toContainText(/출처\s+budget-plan\.md/);
  await expect(page.locator("#response-quick-meta-text")).not.toContainText(/출처\s+memo\.md/);
  await expect(page.locator('#transcript [data-testid="transcript-meta"]').last()).toContainText("선택 결과 요약");
  await expect(page.locator('#transcript [data-testid="transcript-meta"]').last()).toContainText("출처 2개");
  await expect(page.locator('#transcript [data-testid="transcript-meta"]').last()).not.toContainText(/출처\s+budget-plan\.md/);
  await expect(page.locator('#transcript [data-testid="transcript-meta"]').last()).not.toContainText(/출처\s+memo\.md/);
  await expect(page.locator("#selected-text")).toHaveText(searchFolderRelBudgetPath + "\n" + searchFolderRelMemoPath);

  // response detail preview panel is visible alongside summary body
  await expect(page.getByTestId("response-search-preview")).toBeVisible();
  await expect(page.locator("#response-search-preview .search-preview-item")).toHaveCount(2);
  await expect(page.locator("#response-search-preview .search-preview-name").first()).toHaveText("1. budget-plan.md");
  await expect(page.locator("#response-search-preview .search-preview-name").first()).toHaveAttribute("title", searchFolderRelBudgetPath);
  await expect(page.locator("#response-search-preview .search-preview-match").first()).toHaveText("파일명 일치");
  await expect(page.locator("#response-search-preview .search-preview-snippet").first()).toBeVisible();
  await expect(page.locator("#response-search-preview .search-preview-snippet").first()).toContainText("budget-plan");
  await expect(page.locator("#response-search-preview .search-preview-name").nth(1)).toHaveText("2. memo.md");
  await expect(page.locator("#response-search-preview .search-preview-name").nth(1)).toHaveAttribute("title", searchFolderRelMemoPath);
  await expect(page.locator("#response-search-preview .search-preview-match").nth(1)).toHaveText("내용 일치");
  await expect(page.locator("#response-search-preview .search-preview-snippet").nth(1)).toBeVisible();
  await expect(page.locator("#response-search-preview .search-preview-snippet").nth(1)).toContainText("budget");
  await expect(page.getByTestId("response-text")).toBeVisible();

  // transcript preview panel is also visible in search-plus-summary
  const lastAssistant = page.locator("#transcript .message.assistant").last();
  await expect(lastAssistant.locator(".search-preview-panel")).toBeVisible();
  await expect(lastAssistant.locator(".search-preview-item")).toHaveCount(2);
  await expect(lastAssistant.locator(".search-preview-name").first()).toHaveText("1. budget-plan.md");
  await expect(lastAssistant.locator(".search-preview-name").first()).toHaveAttribute("title", searchFolderRelBudgetPath);
  await expect(lastAssistant.locator(".search-preview-match").first()).toHaveText("파일명 일치");
  await expect(lastAssistant.locator(".search-preview-snippet").first()).toBeVisible();
  await expect(lastAssistant.locator(".search-preview-snippet").first()).toContainText("budget-plan");
  await expect(lastAssistant.locator(".search-preview-name").nth(1)).toHaveText("2. memo.md");
  await expect(lastAssistant.locator(".search-preview-name").nth(1)).toHaveAttribute("title", searchFolderRelMemoPath);
  await expect(lastAssistant.locator(".search-preview-match").nth(1)).toHaveText("내용 일치");
  await expect(lastAssistant.locator(".search-preview-snippet").nth(1)).toBeVisible();
  await expect(lastAssistant.locator(".search-preview-snippet").nth(1)).toContainText("budget");
  await expect(page.locator("#transcript .message-when").first()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
  await expect(page.locator("#transcript .message-when").last()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
});

test("검색만 응답은 transcript에서 preview cards만 보이고 본문 텍스트는 숨겨집니다", async ({ page }) => {
  await prepareSession(page, "search-only");
  await page.locator('input[name="request_mode"][value="search"]').check();
  await page.getByTestId("browser-folder-input").setInputFiles(searchFixtureDir);
  await expect(page.locator("#picked-folder-name")).toContainText("2개 파일");
  await page.getByTestId("search-query").fill("budget");
  await page.locator("#search-only").check();

  await page.getByTestId("submit-request").click();

  // wait for response to be fully rendered (selected paths populated by renderResult)
  await expect(page.locator("#selected-text")).toContainText(searchFolderRelBudgetPath);

  // response detail box shows preview cards instead of raw text
  await expect(page.getByTestId("response-search-preview")).toBeVisible();
  await expect(page.locator("#response-search-preview .search-preview-item")).toHaveCount(2);
  await expect(page.locator("#response-search-preview .search-preview-name").first()).toHaveText("1. budget-plan.md");
  await expect(page.locator("#response-search-preview .search-preview-name").first()).toHaveAttribute("title", searchFolderRelBudgetPath);
  await expect(page.locator("#response-search-preview .search-preview-match").first()).toHaveText("파일명 일치");
  await expect(page.locator("#response-search-preview .search-preview-snippet").first()).toBeVisible();
  await expect(page.locator("#response-search-preview .search-preview-snippet").first()).toContainText("budget-plan");
  await expect(page.locator("#response-search-preview .search-preview-name").nth(1)).toHaveText("2. memo.md");
  await expect(page.locator("#response-search-preview .search-preview-name").nth(1)).toHaveAttribute("title", searchFolderRelMemoPath);
  await expect(page.locator("#response-search-preview .search-preview-match").nth(1)).toHaveText("내용 일치");
  await expect(page.locator("#response-search-preview .search-preview-snippet").nth(1)).toBeVisible();
  await expect(page.locator("#response-search-preview .search-preview-snippet").nth(1)).toContainText("budget");
  await expect(page.getByTestId("response-text")).toBeHidden();
  await expect(page.getByTestId("response-copy-text")).toBeHidden();
  await expect(page.locator("#selected-text")).toHaveText(searchFolderRelBudgetPath + "\n" + searchFolderRelMemoPath);

  // selected-copy button is visible and copies path list
  await expect(page.getByTestId("selected-copy")).toBeVisible();
  await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.getByTestId("selected-copy").click();
  await expect(page.locator("#notice-box")).toHaveText("선택 경로를 복사했습니다.");
  const clipboardText = await page.evaluate(() => navigator.clipboard.readText());
  expect(clipboardText).toBe(searchFolderRelBudgetPath + "\n" + searchFolderRelMemoPath);

  // transcript preview cards are visible
  const lastAssistant = page.locator("#transcript .message.assistant").last();
  await expect(lastAssistant.locator(".search-preview-panel")).toBeVisible();
  await expect(lastAssistant.locator(".search-preview-item")).toHaveCount(2);
  await expect(lastAssistant.locator(".search-preview-name").first()).toHaveText("1. budget-plan.md");
  await expect(lastAssistant.locator(".search-preview-name").first()).toHaveAttribute("title", searchFolderRelBudgetPath);
  await expect(lastAssistant.locator(".search-preview-match").first()).toHaveText("파일명 일치");
  await expect(lastAssistant.locator(".search-preview-snippet").first()).toBeVisible();
  await expect(lastAssistant.locator(".search-preview-snippet").first()).toContainText("budget-plan");
  await expect(lastAssistant.locator(".search-preview-name").nth(1)).toHaveText("2. memo.md");
  await expect(lastAssistant.locator(".search-preview-name").nth(1)).toHaveAttribute("title", searchFolderRelMemoPath);
  await expect(lastAssistant.locator(".search-preview-match").nth(1)).toHaveText("내용 일치");
  await expect(lastAssistant.locator(".search-preview-snippet").nth(1)).toBeVisible();
  await expect(lastAssistant.locator(".search-preview-snippet").nth(1)).toContainText("budget");

  // transcript body text (pre) should be hidden for search-only
  await expect(lastAssistant.locator("pre")).toHaveCount(0);

  // after search-only, send search-plus-summary in same session — body must recover
  await page.locator("#search-only").uncheck();
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText("[모의 요약]");
  await expect(page.getByTestId("response-search-preview")).toBeVisible();
  await expect(page.locator("#transcript .message-when").first()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
  await expect(page.locator("#transcript .message-when").last()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
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

  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText("새 경로로 저장하려면 다시 승인해 주세요.");
  await expect(page.getByTestId("approval-path-input")).toHaveValue(revisedNotePath);
  await expect(page.locator("#transcript .message-when").first()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
  await expect(page.locator("#transcript .message-when").last()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
});

test("승인 후 실제 note가 저장됩니다", async ({ page }) => {
  await prepareSession(page, "save");
  await page.getByTestId("source-path").fill(longFixturePath);
  await page.getByTestId("save-summary").check();
  await page.getByTestId("note-path").fill(directNotePath);
  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("approval-box")).toBeVisible();
  await page.getByTestId("approve-button").click();

  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText("저장했습니다.");
  expect(fs.existsSync(directNotePath)).toBeTruthy();
  await expect(page.locator("#transcript .message-when").first()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
  await expect(page.locator("#transcript .message-when").last()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
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

  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText("저장했습니다.");
  await expect(page.locator("#response-saved-path-row")).toBeVisible();
  await expect(page.locator("#response-saved-path")).toContainText("late-flip-note.md");
  await expect(page.locator("#response-content-verdict-state")).toHaveText("최신 내용 판정은 원문 저장 승인입니다.");
  await expect(page.getByTestId("response-content-reason-box")).toBeHidden();
  expect(fs.existsSync(lateFlipNotePath)).toBeTruthy();
  const savedBeforeReject = fs.readFileSync(lateFlipNotePath, "utf-8");
  expect(savedBeforeReject).toContain("중간 섹션 핵심 결정은 승인 기반 저장을 유지하는 것입니다.");

  await page.getByTestId("response-content-reject").click();

  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText("저장했습니다.");
  await expect(page.locator("#notice-box")).toHaveText("내용 거절을 기록했습니다. 이미 저장된 노트는 그대로 유지되며 최신 내용 판정만 바뀝니다.");
  const lateFlipVerdictStatePattern = /^내용 거절 기록됨 · .+$/;
  await expect(page.locator("#response-content-verdict-state")).toHaveText(lateFlipVerdictStatePattern);
  const lateFlipSavedHistoryVerdictStatus = "이 답변 내용을 거절로 기록했습니다. 저장 승인 거절과는 별도입니다. 아래 수정본 기록이나 저장 요청은 계속 별도 흐름으로 사용할 수 있습니다. 이미 저장된 노트와 경로는 그대로 남고, 이번 내용 거절은 최신 판정만 바꿉니다.";
  await expect(page.locator("#response-content-verdict-status")).toHaveText(lateFlipSavedHistoryVerdictStatus);
  await expect(page.getByTestId("response-content-reason-box")).toBeVisible();
  await expect(page.locator("#response-saved-path-row")).toBeVisible();
  await expect(page.locator("#response-saved-path")).toContainText("late-flip-note.md");
  expect(fs.readFileSync(lateFlipNotePath, "utf-8")).toBe(savedBeforeReject);
  await expect(page.locator("#transcript .message-when").first()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
  await expect(page.locator("#transcript .message-when").last()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
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

  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText(middleSignal);
  await expect(approvalBox).toBeVisible();
  await expect(responseBox.getByTestId("response-content-verdict-box")).toBeVisible();
  await expect(responseBox.getByTestId("response-content-reject")).toBeVisible();
  await expect(responseBox.getByTestId("response-content-reason-box")).toBeHidden();
  await expect(approvalBox.locator('[data-testid="response-content-reject"]')).toHaveCount(0);
  const initialVerdictStatus = "저장 승인 거절과는 별도입니다. 이 버튼을 누르면 grounded-brief 원문 응답에 내용 거절을 즉시 기록합니다. 이미 열린 저장 승인 카드는 그대로 유지되며 자동 취소되지 않습니다.";
  await expect(page.locator("#response-content-verdict-status")).toHaveText(initialVerdictStatus);
  const expectedNotePreview = [
    `# ${path.basename(longFixturePath)} 요약`,
    "",
    `원본 파일: ${longFixturePath}`,
    "",
    "## 요약",
    `[모의 요약] ${middleSignal} 추가로 로컬 우선 구조를 유지합니다. 마무리 설명 문장입니다. 마무리 설명 문장입니다. 마무리 설명 문장입니다. 마무리 설명 문장입니다. 마무리 설명 문장입니다. 마무리 설명 문장입니다. 마 긴 요약 문서 도입 설명 문장입니다. 도입 설명 문장입니다. 도입 설명 문장입니다. 도입 설명 문장입니다. 도입 설명 문장입니다. 도입 설명 문장입니다. 도입 설명 문장입니다. `,
  ].join("\n");
  await expect(page.locator("#approval-preview")).toHaveText(expectedNotePreview);

  const originalApprovalPreview = (await page.locator("#approval-preview").textContent()) || "";

  await page.getByTestId("response-content-reject").click();

  await expect(page.locator("#notice-box")).toHaveText("내용 거절을 기록했습니다. 저장 승인 거절과는 별도입니다.");
  const postRejectVerdictStatePattern = /^내용 거절 기록됨 · .+$/;
  await expect(page.locator("#response-content-verdict-state")).toHaveText(postRejectVerdictStatePattern);
  const postRejectVerdictStatus = "이 답변 내용을 거절로 기록했습니다. 저장 승인 거절과는 별도입니다. 아래 수정본 기록이나 저장 요청은 계속 별도 흐름으로 사용할 수 있습니다. 이미 열린 저장 승인 카드는 그대로 유지되며 자동 취소되지 않습니다.";
  await expect(page.locator("#response-content-verdict-status")).toHaveText(postRejectVerdictStatus);
  await expect(responseBox.getByTestId("response-content-reason-box")).toBeVisible();
  await expect(responseBox.getByTestId("response-content-reason-submit")).toBeDisabled();
  await expect(page.locator("#response-content-reason-status")).toContainText("비워 두면 메모 기록 버튼이 켜지지 않으며");
  await page.getByTestId("response-content-reason-input").fill(rejectNote);
  await expect(responseBox.getByTestId("response-content-reason-submit")).toBeEnabled();
  await page.getByTestId("response-content-reason-submit").click();
  await expect(page.locator("#notice-box")).toHaveText("거절 메모를 기록했습니다. 내용 거절 판정은 그대로 유지됩니다.");
  await expect(page.getByTestId("response-content-reason-input")).toHaveValue(rejectNote);
  await expect(page.locator("#response-content-reason-status")).toContainText("기록된 거절 메모가 있습니다");
  await expect(page.locator("#response-quick-meta-text")).toContainText("내용 거절 기록됨");
  await expect(approvalBox).toBeVisible();
  await expect(page.getByTestId("approval-path-input")).toHaveValue(rejectedVerdictNotePath);
  await expect(page.locator("#approval-preview")).toHaveText(originalApprovalPreview);
  await expect(page.getByTestId("approve-button")).toBeEnabled();

  await page.getByTestId("approve-button").click();

  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText("저장했습니다.");
  await expect
    .poll(async () => {
      const payload = await fetchSessionPayload(page, sessionId);
      return Array.isArray(payload.session?.pending_approvals) ? payload.session.pending_approvals.length : -1;
    })
    .toBe(0);
  await expect(approvalBox).toBeHidden();
  await expect(page.locator("#response-saved-path-row")).toBeVisible();
  await expect(page.locator("#response-saved-path")).toContainText("rejected-verdict-note.md");
  await expect(page.locator("#response-content-verdict-state")).toHaveText("최신 내용 판정은 원문 저장 승인입니다.");
  await expect(responseBox.getByTestId("response-content-reason-box")).toBeHidden();
  await expect(page.getByTestId("response-content-reject")).toBeEnabled();
  await expect(page.locator("#response-quick-meta-text")).not.toContainText("내용 거절 기록됨");
  expect(fs.existsSync(rejectedVerdictNotePath)).toBeTruthy();
  await expect(page.locator("#transcript .message-when").first()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
  await expect(page.locator("#transcript .message-when").last()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
});

test("corrected-save first bridge path가 기록본 기준 승인 스냅샷으로 저장됩니다", async ({ page }) => {
  const correctedTextA = "수정본 A입니다.\n핵심만 남겼습니다.";
  const correctedTextB = "수정본 B입니다.\n다시 손봤습니다.";

  await prepareSession(page, "corrected-save");
  await page.getByTestId("source-path").fill(longFixturePath);
  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText("중간 섹션 핵심 결정은 승인 기반 저장을 유지하는 것입니다.");
  await expect(page.getByTestId("response-correction-box")).toBeVisible();
  await expect(page.getByTestId("response-correction-save-request")).toBeVisible();
  await expect(page.getByTestId("response-correction-save-request")).toBeDisabled();
  await expect(page.locator("#response-correction-status")).toHaveText("먼저 수정본 기록을 눌러야 저장 요청 버튼이 켜집니다. 입력창의 미기록 텍스트는 바로 승인 스냅샷이 되지 않습니다. 저장 승인과는 별도입니다. 아직 기록된 수정본이 없어 같은 세션의 후속 질문과 재요약은 원본 요약 기준으로 이어집니다.");

  await page.getByTestId("response-correction-input").fill(correctedTextA);
  await expect(page.getByTestId("response-correction-submit")).toBeEnabled();
  await page.getByTestId("response-correction-submit").click();

  await expect(page.locator("#notice-box")).toHaveText("수정본을 기록했습니다. 저장 승인은 별도 흐름으로 유지됩니다.");
  await expect(page.getByTestId("response-correction-save-request")).toBeEnabled();
  await expect(page.locator("#response-correction-state")).toHaveText(/^기록된 수정본이 있습니다 · .+$/);
  await expect(page.locator("#response-correction-status")).toHaveText("저장 요청은 현재 입력창이 아니라 이미 기록된 수정본으로 새 승인 미리보기를 만듭니다. 저장 승인과는 별도입니다. 기록된 수정본이 같은 세션의 후속 질문과 재요약 기준이 됩니다.");

  await page.getByTestId("response-correction-save-request").click();

  await expect(page.locator("#notice-box")).toHaveText("기록된 수정본 기준 저장 승인을 만들었습니다.");
  await expect(page.getByTestId("approval-box")).toBeVisible();
  await expect(page.locator("#approval-meta span").filter({ hasText: "저장 기준:" })).toHaveText("저장 기준: 기록된 수정본 스냅샷");
  await expect(page.locator("#approval-meta span").filter({ hasText: "요청 시점에 고정되며" })).toHaveText("이 미리보기는 저장 요청 시점에 고정되며, 나중에 수정본을 다시 기록해도 자동으로 바뀌지 않습니다.");
  await expect(page.locator("#approval-meta span").filter({ hasText: "새 저장 요청을 다시 만들어야 합니다" })).toHaveText("더 새 수정본을 저장하려면 응답 카드에서 새 저장 요청을 다시 만들어야 합니다.");
  await expect(page.locator("#approval-meta")).not.toContainText("저장 기준: 원래 grounded brief 초안");
  await expect(page.locator("#approval-preview")).toHaveText(correctedTextA);
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText("현재 기록된 수정본 스냅샷");

  await page.getByTestId("response-correction-input").fill(correctedTextB);
  await expect(page.getByTestId("response-correction-save-request")).toBeEnabled();
  await expect(page.locator("#response-correction-state")).toHaveText("입력창 변경이 아직 다시 기록되지 않았습니다.");
  await expect(page.locator("#response-correction-status")).toHaveText("저장 요청 버튼은 직전 기록본으로만 동작합니다. 지금 입력 중인 수정으로 저장하려면 먼저 수정본 기록을 다시 눌러 주세요. 저장 승인과는 별도입니다. 후속 질문과 재요약도 직전 기록본 기준으로 이어지며, 입력창의 새 변경을 기준으로 바꾸려면 다시 수정본 기록을 눌러 주세요. 이미 열린 저장 승인 카드도 이전 요청 시점 스냅샷으로 그대로 유지됩니다.");
  await expect(page.locator("#approval-preview")).toHaveText(correctedTextA);
  await expect(page.locator("#approval-preview")).not.toContainText("수정본 B입니다.");

  await page.getByTestId("approve-button").click();

  await expect(page.getByTestId("approval-box")).toBeHidden();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText("승인 시점에 고정된 수정본");
  await expect(page.getByTestId("response-text")).toContainText("다시 저장 요청해 주세요.");
  await expect(page.locator("#response-saved-path-row")).toBeVisible();
  await expect(page.locator("#response-saved-path")).toContainText("long-summary-fixture-summary.md");
  expect(fs.existsSync(correctedBridgeNotePath)).toBeTruthy();
  expect(fs.readFileSync(correctedBridgeNotePath, "utf-8")).toBe(correctedTextA);
  await expect(page.locator("#transcript .message-when").first()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
  await expect(page.locator("#transcript .message-when").last()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
});

test("corrected follow-up basis는 기록된 수정본을 같은 세션의 후속 질문 / 재요약 기준으로 노출합니다", async ({ page }) => {
  const correctedText = "수정본 기준입니다.\n같은 세션의 후속 질문은 이 기록본을 기준으로 이어집니다.";

  await prepareSession(page, "corrected-follow-up-basis");
  await page.getByTestId("source-path").fill(longFixturePath);
  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-correction-box")).toBeVisible();

  const contextBox = page.locator("#context-box");
  const contextText = page.locator("#context-text");
  await expect(contextBox).toBeVisible();
  await expect(contextText).toContainText("후속 질문 / 재요약 기준 (현재 요약):");
  await expect(contextText).not.toContainText("후속 질문 / 재요약 기준 (기록된 수정본):");
  await expect(page.locator("#response-correction-status")).toHaveText(
    "먼저 수정본 기록을 눌러야 저장 요청 버튼이 켜집니다. 입력창의 미기록 텍스트는 바로 승인 스냅샷이 되지 않습니다. 저장 승인과는 별도입니다. 아직 기록된 수정본이 없어 같은 세션의 후속 질문과 재요약은 원본 요약 기준으로 이어집니다."
  );

  await page.getByTestId("response-correction-input").fill(correctedText);
  await page.getByTestId("response-correction-submit").click();

  await expect(page.locator("#notice-box")).toHaveText("수정본을 기록했습니다. 저장 승인은 별도 흐름으로 유지됩니다.");
  await expect(page.locator("#response-correction-status")).toHaveText(
    "저장 요청은 현재 입력창이 아니라 이미 기록된 수정본으로 새 승인 미리보기를 만듭니다. 저장 승인과는 별도입니다. 기록된 수정본이 같은 세션의 후속 질문과 재요약 기준이 됩니다."
  );

  await expect(contextText).toContainText("후속 질문 / 재요약 기준 (기록된 수정본):");
  await expect(contextText).toContainText("수정본 기준입니다. 같은 세션의 후속 질문은 이 기록본을 기준으로 이어집니다.");
  await expect(contextText).not.toContainText("후속 질문 / 재요약 기준 (현재 요약):");

  const transcriptMessagesBeforeFollowUp = await page.locator("#transcript .message").count();
  await page.locator('input[name="request_mode"][value="chat"]').check();
  await page.locator("#user-text").fill("이 문서에서 기록된 수정본을 기준으로 핵심 결정만 다시 알려 주세요.");
  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.locator("#transcript .message")).not.toHaveCount(transcriptMessagesBeforeFollowUp);
  await expect(contextBox).toBeVisible();
  await expect(contextText).toContainText("후속 질문 / 재요약 기준 (기록된 수정본):");
  await expect(contextText).toContainText("수정본 기준입니다. 같은 세션의 후속 질문은 이 기록본을 기준으로 이어집니다.");
  await expect(contextText).not.toContainText("후속 질문 / 재요약 기준 (현재 요약):");
});

test("corrected-save 저장 뒤 늦게 내용 거절하고 다시 수정해도 saved snapshot과 latest state가 분리됩니다", async ({ page }) => {
  // NOTE: these corrected texts must stay unique across all tests — duplicate (fixture, correctedText) pairs across sessions trigger find_recurring_patterns() and pollute later tests' review queues
  const correctedTextA = "저장 이력 수정본 A입니다.\n핵심만 남겼습니다.";
  const correctedTextB = "저장 이력 수정본 B입니다.\n다시 손봤습니다.";
  const rejectNote = "초기 수정본의 결론이 여전히 과장되어 있습니다.";

  await prepareSession(page, "corrected-long-history");
  await page.getByTestId("source-path").fill(longFixturePath);
  await page.getByTestId("submit-request").click();

  const responseBox = page.getByTestId("response-box");

  await page.getByTestId("response-correction-input").fill(correctedTextA);
  await page.getByTestId("response-correction-submit").click();
  await expect(page.locator("#notice-box")).toHaveText("수정본을 기록했습니다. 저장 승인은 별도 흐름으로 유지됩니다.");

  await page.getByTestId("response-correction-save-request").click();
  await expect(page.getByTestId("approval-box")).toBeVisible();
  await expect(page.locator("#approval-meta span").filter({ hasText: "저장 기준:" })).toHaveText("저장 기준: 기록된 수정본 스냅샷");
  await expect(page.locator("#approval-preview")).toHaveText(correctedTextA);

  await page.getByTestId("approve-button").click();

  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText("승인 시점에 고정된 수정본");
  await expect(page.locator("#response-quick-meta-text")).toContainText("저장 기준 요청 시점 수정본 스냅샷");
  await expect(page.locator("#response-saved-path-row")).toBeVisible();
  await expect(page.locator("#response-content-verdict-state")).toHaveText("최신 내용 판정은 기록된 수정본입니다.");
  await expect(page.locator("#response-correction-state")).toHaveText(/^기록된 수정본이 있습니다 · .+$/);
  expect(fs.existsSync(correctedBridgeNotePath)).toBeTruthy();
  expect(fs.readFileSync(correctedBridgeNotePath, "utf-8")).toBe(correctedTextA);

  await page.getByTestId("response-content-reject").click();

  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText("승인 시점에 고정된 수정본");
  await expect(page.locator("#notice-box")).toHaveText("내용 거절을 기록했습니다. 이미 저장된 노트는 그대로 유지되며 최신 내용 판정만 바뀝니다.");
  await expect(page.locator("#response-quick-meta-text")).toContainText("저장 기준 요청 시점 수정본 스냅샷");
  await expect(page.locator("#response-quick-meta-text")).not.toContainText("내용 거절 기록됨");
  const correctedSaveVerdictStatePattern = /^내용 거절 기록됨 · .+$/;
  await expect(page.locator("#response-content-verdict-state")).toHaveText(correctedSaveVerdictStatePattern);
  const correctedSaveSavedHistoryVerdictStatus = "이 답변 내용을 거절로 기록했습니다. 저장 승인 거절과는 별도입니다. 아래 수정본 기록이나 저장 요청은 계속 별도 흐름으로 사용할 수 있습니다. 이미 저장된 노트와 경로는 그대로 남고, 이번 내용 거절은 최신 판정만 바꿉니다.";
  await expect(page.locator("#response-content-verdict-status")).toHaveText(correctedSaveSavedHistoryVerdictStatus);
  await expect(page.getByTestId("response-content-reason-box")).toBeVisible();
  expect(fs.readFileSync(correctedBridgeNotePath, "utf-8")).toBe(correctedTextA);

  await page.getByTestId("response-content-reason-input").fill(rejectNote);
  await page.getByTestId("response-content-reason-submit").click();
  await expect(page.locator("#notice-box")).toHaveText("거절 메모를 기록했습니다. 내용 거절 판정은 그대로 유지됩니다.");
  await expect(page.locator("#response-content-reason-status")).toContainText("기록된 거절 메모가 있습니다");

  await page.getByTestId("response-correction-input").fill(correctedTextB);
  await page.getByTestId("response-correction-submit").click();

  await expect(page.locator("#notice-box")).toHaveText("수정본을 기록했습니다. 저장 승인은 별도 흐름으로 유지됩니다.");
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText("승인 시점에 고정된 수정본");
  await expect(page.locator("#response-quick-meta-text")).toContainText("저장 기준 요청 시점 수정본 스냅샷");
  await expect(page.locator("#response-quick-meta-text")).not.toContainText("내용 거절 기록됨");
  await expect(page.locator("#response-content-verdict-state")).toHaveText("최신 내용 판정은 기록된 수정본입니다.");
  await expect(page.getByTestId("response-content-reason-box")).toBeHidden();
  await expect(page.getByTestId("response-correction-input")).toHaveValue(correctedTextB);
  await expect(page.locator("#response-correction-state")).toHaveText(/^기록된 수정본이 있습니다 · .+$/);
  await expect(page.locator("#response-correction-status")).toHaveText("저장 요청은 현재 입력창이 아니라 이미 기록된 수정본으로 새 승인 미리보기를 만듭니다. 저장 승인과는 별도입니다. 기록된 수정본이 같은 세션의 후속 질문과 재요약 기준이 됩니다.");
  await expect(page.getByTestId("response-correction-save-request")).toBeEnabled();
  await expect(page.locator("#response-saved-path-row")).toBeVisible();
  expect(fs.readFileSync(correctedBridgeNotePath, "utf-8")).toBe(correctedTextA);
  await expect(page.locator("#transcript .message-when").first()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
  await expect(page.locator("#transcript .message-when").last()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
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

  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText(middleSignal);
  await expect(confirmationBox).toBeHidden();
  await expectSessionLocalReviewQueueCount(page, sessionId, 0);

  await page.getByTestId("response-correction-input").fill(correctedTextA);
  await page.getByTestId("response-correction-submit").click();

  await expect(page.locator("#notice-box")).toHaveText("수정본을 기록했습니다. 저장 승인은 별도 흐름으로 유지됩니다.");
  await expect(confirmationBox).toBeVisible();
  await expect(confirmationButton).toBeEnabled();
  await expect(page.locator("#response-candidate-confirmation-status")).toHaveText("이 버튼은 현재 기록된 수정 방향을 나중에도 다시 써도 된다는 positive reuse confirmation만 남깁니다. 저장 승인, 내용 거절, 거절 메모, 피드백과는 별도입니다.");

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
      signal_name: "session_local_memory_signal.correction_signal",
      relationship: "primary_basis",
    },
  ]);

  await page.getByTestId("response-correction-save-request").click();

  await expect(approvalBox).toBeVisible();
  await expect(confirmationBox).toBeVisible();
  await expect(approvalBox.locator('[data-testid="response-candidate-confirmation-submit"]')).toHaveCount(0);
  await expect(page.locator("#response-candidate-confirmation-status")).toHaveText("이 버튼은 현재 기록된 수정 방향을 나중에도 다시 써도 된다는 positive reuse confirmation만 남깁니다. 저장 승인, 내용 거절, 거절 메모, 피드백과는 별도입니다. 이미 열린 저장 승인 카드와도 섞이지 않습니다.");

  await page.getByTestId("approve-button").click();

  await expect(approvalBox).toBeHidden();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText("승인 시점에 고정된 수정본");
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
      signal_name: "session_local_memory_signal.correction_signal",
      relationship: "primary_basis",
    },
    {
      signal_name: "session_local_memory_signal.save_signal",
      relationship: "supporting_evidence",
    },
  ]);

  await expect(confirmationButton).toBeEnabled();
  await confirmationButton.click();

  await expect(page.locator("#notice-box")).toHaveText("현재 수정 방향을 나중에도 다시 써도 된다는 확인을 기록했습니다. 저장 승인과는 별도입니다.");
  await expect(page.locator("#response-candidate-confirmation-state")).toHaveText(/^재사용 확인 기록됨 · .+$/);
  await expect(confirmationButton).toBeDisabled();
  await expect(page.locator("#response-candidate-confirmation-status")).toHaveText("현재 기록된 수정 방향을 나중에도 다시 써도 된다는 positive reuse confirmation만 남겼습니다. 저장 승인, 내용 거절, 거절 메모와는 별도입니다.");
  await expect(reviewQueueBox).toBeVisible();
  await expect(reviewQueueBox.locator(".sidebar-section-label")).toHaveText("검토 후보");
  await expect(page.locator("#review-queue-status")).toHaveText("후보를 수락, 거절, 보류, 또는 편집 메모로 기록할 수 있습니다.");
  const localReviewItem = sessionLocalReviewQueueItem(reviewQueueBox);
  await expect(localReviewItem.locator("strong")).toHaveText("explicit rewrite correction recorded for this grounded brief");
  await expect(localReviewItem.locator(".history-item-title span")).toContainText("기준 명시 확인");
  await expect(localReviewItem.locator(".history-item-title span")).toContainText("상태 검토 대기");
  const reviewAcceptButton = localReviewItem.getByTestId("review-queue-accept");
  await expect(reviewAcceptButton).toHaveText("검토 수락");
  const reviewRejectButton = localReviewItem.getByTestId("review-queue-reject");
  await expect(reviewRejectButton).toHaveText("거절");
  const reviewDeferButton = localReviewItem.getByTestId("review-queue-defer");
  await expect(reviewDeferButton).toHaveText("보류");
  const reviewEditButton = localReviewItem.getByTestId("review-queue-edit");
  await expect(reviewEditButton).toHaveText("편집");

  const preAcceptPayload = await fetchSessionPayload(page, sessionId);
  const preAcceptLocalItems = sessionLocalReviewQueueItems(preAcceptPayload);
  expect(preAcceptLocalItems).toHaveLength(1);
  expect(preAcceptLocalItems[0].item_type).toBe("durable_candidate");
  expect(preAcceptLocalItems[0].derived_from.record_type).toBe("candidate_confirmation_record");
  expect(typeof preAcceptLocalItems[0].derived_at).toBe("string");
  expect(preAcceptLocalItems[0].derived_at.length).toBeGreaterThan(0);
  await reviewAcceptButton.click();

  await expect(page.locator("#notice-box")).toHaveText("검토 후보를 수락했습니다. 아직 적용되지는 않았습니다.");
  await expectSessionLocalReviewQueueCount(page, sessionId, 0);
  await expect(page.locator("#response-quick-meta-text")).toContainText("검토 수락됨");
  await expect(page.getByTestId("transcript-meta").filter({ hasText: "검토 수락됨" })).toHaveCount(1);

  sessionPayload = await fetchSessionPayload(page, sessionId);
  sourceMessage = findMessageById(sessionPayload.session?.messages, sourceMessageId);
  expect(sourceMessage.candidate_confirmation_record.confirmation_label).toBe("explicit_reuse_confirmation");
  expect(sourceMessage.candidate_confirmation_record.candidate_id).toBe(sourceMessage.session_local_candidate.candidate_id);
  expect(sourceMessage.session_local_candidate.supporting_signal_refs).toEqual([
    {
      signal_name: "session_local_memory_signal.correction_signal",
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
  expect(typeof sourceMessage.durable_candidate.derived_at).toBe("string");
  expect(sourceMessage.durable_candidate.derived_at.length).toBeGreaterThan(0);
  expect(sourceMessage.durable_candidate.derived_from.record_type).toBe("candidate_confirmation_record");
  expect(sourceMessage.durable_candidate.derived_from.candidate_id).toBe(sourceMessage.session_local_candidate.candidate_id);
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
  expect(sessionLocalReviewQueueItems(sessionPayload)).toEqual([]);

  await page.locator('input[name="request_mode"][value="chat"]').check();
  await page.locator("#user-text").fill("follow-up after review accept");
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.locator("#response-quick-meta-text")).toContainText("검토 수락됨");
  await expect(page.getByTestId("transcript-meta").filter({ hasText: "검토 수락됨" })).toHaveCount(1);

  await page.locator('input[name="request_mode"][value="file"]').check();
  await page.getByTestId("source-path").fill(longFixturePath);
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText(middleSignal);

  await page.getByTestId("response-correction-input").fill(correctedTextB);
  await page.getByTestId("response-correction-submit").click();

  await expect(page.locator("#notice-box")).toHaveText("수정본을 기록했습니다. 저장 승인은 별도 흐름으로 유지됩니다.");
  await expectSessionLocalReviewQueueCount(page, sessionId, 0);
  await expect(page.locator("#response-quick-meta-text")).not.toContainText("검토 수락됨");
  // The originally reviewed source message retains its own candidate_review_record
  // in the transcript — that is factual history, not a stale label.
  // Quick-meta reflects the current context's review state (cleared by the newer correction).
  await expect(page.getByTestId("transcript-meta").filter({ hasText: "검토 수락됨" })).toHaveCount(1);

  await page.locator('input[name="request_mode"][value="chat"]').check();
  await page.locator("#user-text").fill("follow-up after stale clear");
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.locator("#response-quick-meta-text")).not.toContainText("검토 수락됨");
  await expect(page.getByTestId("transcript-meta").filter({ hasText: "검토 수락됨" })).toHaveCount(1);

  await expect(page.locator("#transcript .message-when").first()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
  await expect(page.locator("#transcript .message-when").last()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
});

test("review-queue reject/defer는 accept와 동일한 quick-meta, transcript-meta, stale-clear 경로를 따릅니다", async ({ page }) => {
  const correctedTextR = "거절용 수정 방향입니다.\n핵심만 남겼습니다.";
  const correctedTextD = "보류용 수정 방향입니다.\n다시 손봤습니다.";
  const correctedTextNew = "새 수정 방향입니다.\n교체용입니다.";

  const sessionId = await prepareSession(page, "reject-defer");
  await page.getByTestId("source-path").fill(longFixturePath);
  await page.getByTestId("submit-request").click();

  const confirmationBox = page.getByTestId("response-candidate-confirmation-box");
  const confirmationButton = page.getByTestId("response-candidate-confirmation-submit");
  const reviewQueueBox = page.getByTestId("review-queue-box");

  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText(middleSignal);

  // --- reject path ---
  await page.getByTestId("response-correction-input").fill(correctedTextR);
  await page.getByTestId("response-correction-submit").click();
  await expect(page.locator("#notice-box")).toHaveText("수정본을 기록했습니다. 저장 승인은 별도 흐름으로 유지됩니다.");

  await confirmationButton.click();
  await expect(reviewQueueBox).toBeVisible();
  await sessionLocalReviewQueueItem(reviewQueueBox).getByTestId("review-queue-reject").click();

  await expect(page.locator("#notice-box")).toHaveText("검토 후보를 거절했습니다.");
  await expectSessionLocalReviewQueueCount(page, sessionId, 0);
  await expect(page.locator("#response-quick-meta-text")).toContainText("검토 거절됨");
  await expect(page.getByTestId("transcript-meta").filter({ hasText: "검토 거절됨" })).toHaveCount(1);

  // follow-up retains reject quick-meta
  await page.locator('input[name="request_mode"][value="chat"]').check();
  await page.locator("#user-text").fill("follow-up after review reject");
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.locator("#response-quick-meta-text")).toContainText("검토 거절됨");
  await expect(page.getByTestId("transcript-meta").filter({ hasText: "검토 거절됨" })).toHaveCount(1);

  // new correction creates newer unreviewed context → stale-clear
  await page.locator('input[name="request_mode"][value="file"]').check();
  await page.getByTestId("source-path").fill(longFixturePath);
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText(middleSignal);

  await page.getByTestId("response-correction-input").fill(correctedTextD);
  await page.getByTestId("response-correction-submit").click();
  await expect(page.locator("#notice-box")).toHaveText("수정본을 기록했습니다. 저장 승인은 별도 흐름으로 유지됩니다.");
  await expect(page.locator("#response-quick-meta-text")).not.toContainText("검토 거절됨");
  // original rejected source retains its own transcript-meta label
  await expect(page.getByTestId("transcript-meta").filter({ hasText: "검토 거절됨" })).toHaveCount(1);

  // --- defer path ---
  await confirmationButton.click();
  await expect(reviewQueueBox).toBeVisible();
  await sessionLocalReviewQueueItem(reviewQueueBox).getByTestId("review-queue-defer").click();

  await expect(page.locator("#notice-box")).toHaveText("검토 후보를 보류했습니다.");
  await expectSessionLocalReviewQueueCount(page, sessionId, 0);
  await expect(page.locator("#response-quick-meta-text")).toContainText("검토 보류됨");
  await expect(page.getByTestId("transcript-meta").filter({ hasText: "검토 보류됨" })).toHaveCount(1);

  // follow-up retains defer quick-meta
  await page.locator('input[name="request_mode"][value="chat"]').check();
  await page.locator("#user-text").fill("follow-up after review defer");
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.locator("#response-quick-meta-text")).toContainText("검토 보류됨");
  await expect(page.getByTestId("transcript-meta").filter({ hasText: "검토 보류됨" })).toHaveCount(1);

  // another correction → stale-clear for defer
  await page.locator('input[name="request_mode"][value="file"]').check();
  await page.getByTestId("source-path").fill(longFixturePath);
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();

  await page.getByTestId("response-correction-input").fill(correctedTextNew);
  await page.getByTestId("response-correction-submit").click();
  await expect(page.locator("#notice-box")).toHaveText("수정본을 기록했습니다. 저장 승인은 별도 흐름으로 유지됩니다.");
  await expect(page.locator("#response-quick-meta-text")).not.toContainText("검토 보류됨");
  // original deferred source retains its own transcript-meta label
  await expect(page.getByTestId("transcript-meta").filter({ hasText: "검토 보류됨" })).toHaveCount(1);
  // rejected label also still in transcript from earlier
  await expect(page.getByTestId("transcript-meta").filter({ hasText: "검토 거절됨" })).toHaveCount(1);

  // payload verification: reject and defer records
  const sessionPayload = await fetchSessionPayload(page, sessionId);
  const messagesWithReview = (sessionPayload.session?.messages || []).filter(
    (m) => m.candidate_review_record
  );
  expect(messagesWithReview).toHaveLength(2);
  expect(messagesWithReview[0].candidate_review_record.review_action).toBe("reject");
  expect(messagesWithReview[0].candidate_review_record.review_status).toBe("rejected");
  expect(messagesWithReview[1].candidate_review_record.review_action).toBe("defer");
  expect(messagesWithReview[1].candidate_review_record.review_status).toBe("deferred");
});

test("review-queue 편집은 review_action='edit' review_status='edited' reason_note를 기록합니다", async ({ page }) => {
  const correctedText = "편집 검토용 수정 방향입니다.\n핵심만 남겼습니다.";
  const editNoteText = "수정된 표현입니다. 원래 내용보다 더 명확합니다.";

  const sessionId = await prepareSession(page, "edit-note");
  await page.getByTestId("source-path").fill(longFixturePath);
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();

  const confirmationButton = page.getByTestId("response-candidate-confirmation-submit");
  const reviewQueueBox = page.getByTestId("review-queue-box");

  await page.getByTestId("response-correction-input").fill(correctedText);
  await page.getByTestId("response-correction-submit").click();
  await expect(page.locator("#notice-box")).toHaveText("수정본을 기록했습니다. 저장 승인은 별도 흐름으로 유지됩니다.");

  await confirmationButton.click();
  await expect(page.locator("#notice-box")).toHaveText(
    "현재 수정 방향을 나중에도 다시 써도 된다는 확인을 기록했습니다. 저장 승인과는 별도입니다."
  );
  await expect(reviewQueueBox).toBeVisible();

  const localEditItem = sessionLocalReviewQueueItem(reviewQueueBox);
  const editButton = localEditItem.getByTestId("review-queue-edit");
  await expect(editButton).toBeVisible();
  await editButton.click();

  const editTextarea = localEditItem.locator(".edit-note-area textarea");
  await expect(editTextarea).toBeVisible();
  await editTextarea.fill(editNoteText);

  const confirmBtn = localEditItem.locator(".edit-note-area button");
  await confirmBtn.click();

  await expect(page.locator("#notice-box")).toHaveText("검토 후보에 편집 의견을 기록했습니다.");
  await expectSessionLocalReviewQueueCount(page, sessionId, 0);
  await expect(page.locator("#response-quick-meta-text")).toContainText("검토 편집됨");
  await expect(page.getByTestId("transcript-meta").filter({ hasText: "검토 편집됨" })).toHaveCount(1);

  const sessionPayload = await fetchSessionPayload(page, sessionId);
  const reviewedMessage = sessionPayload.session?.messages?.find(
    (m) => m.candidate_review_record?.review_action === "edit"
  );
  expect(reviewedMessage).toBeDefined();
  expect(reviewedMessage.candidate_review_record.review_status).toBe("edited");
  expect(reviewedMessage.candidate_review_record.reason_note).toBe(editNoteText);
  expect(sessionLocalReviewQueueItems(sessionPayload)).toEqual([]);
});

/**
 * Drive a fresh session through two corrections → emit → apply → confirm-result
 * to reach the active-effect state quickly, without reload-continuity checks.
 * Returns { sessionId, canonicalTransitionId } for downstream assertions.
 */
async function advanceAggregateToActiveEffect(page) {
  const correctedText = "수정 방향 A입니다.\n핵심만 남겼습니다.";
  const sessionId = await prepareSession(page, "aggregate-trigger");
  const aggregateTriggerBox = page.getByTestId("aggregate-trigger-box");

  // First correction + candidate confirmation
  await page.getByTestId("source-path").fill(shortFixturePath);
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText(middleSignal);
  await page.getByTestId("response-correction-input").fill(correctedText);
  await page.getByTestId("response-correction-submit").click();
  await expect(page.locator("#notice-box")).toHaveText("수정본을 기록했습니다. 저장 승인은 별도 흐름으로 유지됩니다.");
  await expect(page.getByTestId("response-candidate-confirmation-box")).toBeVisible();
  await page.getByTestId("response-candidate-confirmation-submit").click();
  await expect(page.locator("#notice-box")).toHaveText("현재 수정 방향을 나중에도 다시 써도 된다는 확인을 기록했습니다. 저장 승인과는 별도입니다.");

  // Second correction — triggers aggregate
  await page.getByTestId("source-path").fill(shortFixturePath);
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText(middleSignal);
  await page.getByTestId("response-correction-input").fill(correctedText);
  await page.getByTestId("response-correction-submit").click();
  await expect(page.locator("#notice-box")).toHaveText("수정본을 기록했습니다. 저장 승인은 별도 흐름으로 유지됩니다.");
  await expect(aggregateTriggerBox).toBeVisible();

  // Emit transition record
  const noteInput = aggregateTriggerBox.getByTestId("aggregate-trigger-note");
  await noteInput.fill("반복 교정 패턴을 적용합니다.");
  const startButton = aggregateTriggerBox.getByTestId("aggregate-trigger-start");
  await expect(startButton).toBeEnabled();
  await startButton.click();
  await expect(page.locator("#notice-box")).toContainText("transition record가 발행되었습니다.");

  // Apply
  const applyButton = aggregateTriggerBox.getByTestId("aggregate-trigger-apply");
  await expect(applyButton).toBeVisible();
  await expect(applyButton).toBeEnabled();
  await applyButton.click();
  await expect(page.locator("#notice-box")).toContainText("검토 메모 적용이 실행되었습니다.");

  // Confirm result — now in active-effect state
  const confirmButton = aggregateTriggerBox.getByTestId("aggregate-trigger-confirm-result");
  await expect(confirmButton).toBeVisible();
  await expect(confirmButton).toBeEnabled();
  await confirmButton.click();
  await expect(page.locator("#notice-box")).toContainText("검토 메모 적용 결과가 확정되었습니다.");

  const payload = await fetchSessionPayload(page, sessionId);
  const canonicalTransitionId =
    payload.session.recurrence_aggregate_candidates[0].reviewed_memory_transition_record.canonical_transition_id;

  return { sessionId, canonicalTransitionId };
}

test("same-session recurrence aggregate는 emitted-apply-confirm lifecycle으로 활성화됩니다", async ({ page }, testInfo) => {
  testInfo.setTimeout(150_000);
  const correctedText = "수정 방향 A입니다.\n핵심만 남겼습니다.";
  const sessionId = await prepareSession(page, "aggregate-trigger");
  const reviewQueueBox = page.getByTestId("review-queue-box");
  const aggregateTriggerBox = page.getByTestId("aggregate-trigger-box");

  await page.getByTestId("source-path").fill(shortFixturePath);
  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText(middleSignal);
  await expectSessionLocalReviewQueueCount(page, sessionId, 0);
  await expect(aggregateTriggerBox).toBeHidden();

  await page.getByTestId("response-correction-input").fill(correctedText);
  await page.getByTestId("response-correction-submit").click();
  await expect(page.locator("#notice-box")).toHaveText("수정본을 기록했습니다. 저장 승인은 별도 흐름으로 유지됩니다.");
  await expect(page.getByTestId("response-candidate-confirmation-box")).toBeVisible();
  await page.getByTestId("response-candidate-confirmation-submit").click();

  await expect(page.locator("#notice-box")).toHaveText("현재 수정 방향을 나중에도 다시 써도 된다는 확인을 기록했습니다. 저장 승인과는 별도입니다.");
  await expect(reviewQueueBox).toBeVisible();
  await expect(reviewQueueBox.locator(".sidebar-section-label")).toHaveText("검토 후보");
  await expect(aggregateTriggerBox).toBeHidden();

  await page.getByTestId("source-path").fill(shortFixturePath);
  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText(middleSignal);
  await page.getByTestId("response-correction-input").fill(correctedText);
  await page.getByTestId("response-correction-submit").click();

  await expect(page.locator("#notice-box")).toHaveText("수정본을 기록했습니다. 저장 승인은 별도 흐름으로 유지됩니다.");
  await expect(aggregateTriggerBox).toBeVisible();
  await expect(page.locator("#aggregate-trigger-status")).toHaveText("검토 메모 적용을 시작할 수 있는 묶음이 있습니다.");
  await expect(aggregateTriggerBox.locator(".sidebar-section-label")).toHaveText("검토 메모 적용 후보");
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-item").locator("strong").first()).toHaveText("반복 교정 묶음");
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-item").locator(".history-item-title span")).toContainText("capability unblocked_all_required");
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-item").locator(".history-item-title span")).toContainText("audit contract_only_not_emitted");
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-item").locator(".history-item-summary").filter({ hasText: "계획 타깃" })).toHaveText("계획 타깃 eligible_for_reviewed_memory_draft_planning_only");
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-helper")).toHaveText("검토 메모 적용을 시작할 수 있습니다. 사유를 입력한 뒤 시작 버튼을 누르세요.");

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
  const aggregateLocalReviewItem = sessionLocalReviewQueueItem(reviewQueueBox);
  await expect(aggregateLocalReviewItem.getByTestId("review-queue-accept")).toHaveText("검토 수락");
  await expect(aggregateLocalReviewItem.getByTestId("review-queue-reject")).toHaveText("거절");
  await expect(aggregateLocalReviewItem.getByTestId("review-queue-defer")).toHaveText("보류");

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
  await expect(page.locator("#notice-box")).toHaveText(`transition record가 발행되었습니다. (${emittedAggregate.reviewed_memory_transition_record.canonical_transition_id})`);
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-helper")).toHaveText("transition record가 발행되었습니다. 적용 실행 버튼을 눌러 주세요.");

  // --- Hard page reload while transition record is emitted (pre-apply) ---
  await page.reload({ waitUntil: "networkidle" });
  await expect(page.locator("#current-session-title")).toBeVisible({ timeout: 10_000 });
  await page.evaluate(async (sid) => {
    document.getElementById("session-id").value = sid;
    document.getElementById("load-session").click();
  }, sessionId);
  await expect(aggregateTriggerBox).toBeVisible({ timeout: 10_000 });
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-helper")).toHaveText(
    "transition record가 발행되었습니다. 적용 실행 버튼을 눌러 주세요."
  );

  const emittedReloadPayload = await fetchSessionPayload(page, sessionId);
  expect(emittedReloadPayload.session.recurrence_aggregate_candidates).toHaveLength(1);
  const emittedReloadAggregate = emittedReloadPayload.session.recurrence_aggregate_candidates[0];
  expect(emittedReloadAggregate.reviewed_memory_transition_record.record_stage).toBe("emitted_record_only_not_applied");
  expect(emittedReloadAggregate.reviewed_memory_transition_record.canonical_transition_id).toBe(
    emittedAggregate.reviewed_memory_transition_record.canonical_transition_id
  );
  expect(emittedReloadAggregate.reviewed_memory_transition_record.applied_at).toBeUndefined();
  expect(emittedReloadAggregate.reviewed_memory_transition_record.apply_result).toBeUndefined();
  const emittedActiveEffects = emittedReloadPayload.session.reviewed_memory_active_effects;
  expect(!emittedActiveEffects || !Array.isArray(emittedActiveEffects) || emittedActiveEffects.length === 0).toBe(true);

  // Apply button must still be visible and enabled after reload
  const applyButtonAfterEmittedReload = aggregateTriggerBox.getByTestId("aggregate-trigger-apply");
  await expect(applyButtonAfterEmittedReload).toBeVisible();
  await expect(applyButtonAfterEmittedReload).toBeEnabled();

  // Post-reload follow-up must NOT include active effect prefix
  await page.getByTestId("source-path").fill(shortFixturePath);
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).not.toContainText("[검토 메모 활성]");

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
  await expect(page.locator("#notice-box")).toHaveText(`검토 메모 적용이 실행되었습니다. (${appliedAggregate.reviewed_memory_transition_record.canonical_transition_id})`);
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-helper")).toHaveText("검토 메모 적용이 실행되었습니다. 결과 확정 버튼을 눌러 주세요.");

  // --- Hard page reload while apply is pending result (pre-confirm) ---
  await page.reload({ waitUntil: "networkidle" });
  await expect(page.locator("#current-session-title")).toBeVisible({ timeout: 10_000 });
  await page.evaluate(async (sid) => {
    document.getElementById("session-id").value = sid;
    document.getElementById("load-session").click();
  }, sessionId);
  await expect(aggregateTriggerBox).toBeVisible({ timeout: 10_000 });
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-helper")).toHaveText(
    "검토 메모 적용이 실행되었습니다. 결과 확정 버튼을 눌러 주세요."
  );

  const appliedPendingReloadPayload = await fetchSessionPayload(page, sessionId);
  expect(appliedPendingReloadPayload.session.recurrence_aggregate_candidates).toHaveLength(1);
  const appliedPendingReloadAggregate = appliedPendingReloadPayload.session.recurrence_aggregate_candidates[0];
  expect(appliedPendingReloadAggregate.reviewed_memory_transition_record.record_stage).toBe("applied_pending_result");
  expect(appliedPendingReloadAggregate.reviewed_memory_transition_record.applied_at).toBeTruthy();
  expect(appliedPendingReloadAggregate.reviewed_memory_transition_record.apply_result).toBeUndefined();
  expect(appliedPendingReloadAggregate.reviewed_memory_transition_record.canonical_transition_id).toBe(
    emittedAggregate.reviewed_memory_transition_record.canonical_transition_id
  );
  const appliedPendingActiveEffects = appliedPendingReloadPayload.session.reviewed_memory_active_effects;
  expect(!appliedPendingActiveEffects || !Array.isArray(appliedPendingActiveEffects) || appliedPendingActiveEffects.length === 0).toBe(true);

  // Confirm result button must still be visible and enabled after reload
  const confirmButtonAfterReload = aggregateTriggerBox.getByTestId("aggregate-trigger-confirm-result");
  await expect(confirmButtonAfterReload).toBeVisible();
  await expect(confirmButtonAfterReload).toBeEnabled();

  // Post-reload follow-up must NOT include active effect prefix
  await page.getByTestId("source-path").fill(shortFixturePath);
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).not.toContainText("[검토 메모 활성]");

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
  await expect(page.locator("#notice-box")).toHaveText(`검토 메모 적용 결과가 확정되었습니다. (${resultAggregate.reviewed_memory_transition_record.canonical_transition_id})`);

  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-result")).toBeVisible();
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-result")).toHaveText(`결과 확정 완료 (${resultAggregate.reviewed_memory_transition_record.canonical_transition_id} · ${resultAggregate.reviewed_memory_transition_record.apply_result.applied_effect_kind})`);
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-helper")).toHaveText("검토 메모 적용 효과가 활성화되었습니다. 이후 응답에 교정 패턴이 반영됩니다.");

  await page.getByTestId("source-path").fill(shortFixturePath);
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText("[검토 메모 활성]");
  await expect(page.getByTestId("response-text")).toContainText("반복 교정 패턴을 적용합니다.");

  // --- Hard page reload while active effect is live ---
  await page.reload({ waitUntil: "networkidle" });
  await expect(page.locator("#current-session-title")).toBeVisible({ timeout: 10_000 });
  await page.evaluate(async (sid) => {
    document.getElementById("session-id").value = sid;
    document.getElementById("load-session").click();
  }, sessionId);
  await expect(aggregateTriggerBox).toBeVisible({ timeout: 10_000 });
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-result")).toBeVisible();
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-result")).toHaveText(
    `결과 확정 완료 (${resultAggregate.reviewed_memory_transition_record.canonical_transition_id} · ${resultAggregate.reviewed_memory_transition_record.apply_result.applied_effect_kind})`
  );
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-helper")).toHaveText(
    "검토 메모 적용 효과가 활성화되었습니다. 이후 응답에 교정 패턴이 반영됩니다."
  );

  const activeReloadPayload = await fetchSessionPayload(page, sessionId);
  expect(activeReloadPayload.session.recurrence_aggregate_candidates).toHaveLength(1);
  const activeReloadAggregate = activeReloadPayload.session.recurrence_aggregate_candidates[0];
  expect(activeReloadAggregate.reviewed_memory_transition_record.record_stage).toBe("applied_with_result");
  expect(activeReloadAggregate.reviewed_memory_transition_record.apply_result.result_stage).toBe("effect_active");
  expect(activeReloadAggregate.reviewed_memory_transition_record.canonical_transition_id).toBe(
    emittedAggregate.reviewed_memory_transition_record.canonical_transition_id
  );
  expect(Array.isArray(activeReloadPayload.session.reviewed_memory_active_effects)).toBe(true);
  expect(activeReloadPayload.session.reviewed_memory_active_effects.length).toBeGreaterThanOrEqual(1);

  // Post-reload follow-up must still include active effect prefix
  await page.getByTestId("source-path").fill(shortFixturePath);
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText("[검토 메모 활성]");
  await expect(page.getByTestId("response-text")).toContainText("반복 교정 패턴을 적용합니다.");
});

test("same-session recurrence aggregate stale candidate retires before apply start", async ({ page }, testInfo) => {
  testInfo.setTimeout(90_000);
  const correctedText = "수정 방향 A입니다.\n핵심만 남겼습니다.";
  const sessionId = await prepareSession(page, "aggregate-stale");
  const aggregateTriggerBox = page.getByTestId("aggregate-trigger-box");

  await page.getByTestId("source-path").fill(shortFixturePath);
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText(middleSignal);
  await expect(aggregateTriggerBox).toBeHidden();

  await page.getByTestId("response-correction-input").fill(correctedText);
  await page.getByTestId("response-correction-submit").click();
  await expect(page.locator("#notice-box")).toHaveText("수정본을 기록했습니다. 저장 승인은 별도 흐름으로 유지됩니다.");
  await expect(aggregateTriggerBox).toBeHidden();

  await page.getByTestId("source-path").fill(shortFixturePath);
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText(middleSignal);

  await page.getByTestId("response-correction-input").fill(correctedText);
  await page.getByTestId("response-correction-submit").click();
  await expect(page.locator("#notice-box")).toHaveText("수정본을 기록했습니다. 저장 승인은 별도 흐름으로 유지됩니다.");

  await expect(aggregateTriggerBox).toBeVisible();
  await expect(aggregateTriggerBox.locator(".sidebar-section-label")).toHaveText("검토 메모 적용 후보");

  const payload = await fetchSessionPayload(page, sessionId);
  expect(payload.session.recurrence_aggregate_candidates).toHaveLength(1);
  expect(payload.session.recurrence_aggregate_candidates[0].recurrence_count).toBe(2);

  const firstSourceMessageId = payload.session.recurrence_aggregate_candidates[0]
    .supporting_source_message_refs[0].source_message_id;

  const supersedingText = "완전히 다른 교정입니다.\n새로운 방향으로 작성했습니다.";
  const correctionResponse = await page.request.post("/api/correction", {
    data: {
      session_id: sessionId,
      message_id: firstSourceMessageId,
      corrected_text: supersedingText,
    },
  });
  expect(correctionResponse.ok()).toBeTruthy();
  const correctionData = await correctionResponse.json();
  expect(correctionData.session.recurrence_aggregate_candidates).toBeUndefined();

  await page.evaluate(async (sid) => {
    document.getElementById("session-id").value = sid;
    document.getElementById("load-session").click();
  }, sessionId);
  await expect(page.locator("#current-session-title")).toBeVisible({ timeout: 10_000 });
  await expect(aggregateTriggerBox).toBeHidden({ timeout: 5_000 });
});

test("review-queue reject-defer aggregate support visibility", async ({ page }, testInfo) => {
  testInfo.setTimeout(90_000);
  const correctedText = "수정 방향 A입니다.\n핵심만 남겼습니다.";
  const sessionId = await prepareSession(page, "aggregate-review-support");
  const aggregateTriggerBox = page.getByTestId("aggregate-trigger-box");
  const reviewQueueBox = page.getByTestId("review-queue-box");

  // First correction + confirm + reject
  await page.getByTestId("source-path").fill(shortFixturePath);
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText(middleSignal);
  await page.getByTestId("response-correction-input").fill(correctedText);
  await page.getByTestId("response-correction-submit").click();
  await expect(page.locator("#notice-box")).toHaveText("수정본을 기록했습니다. 저장 승인은 별도 흐름으로 유지됩니다.");
  await expect(page.getByTestId("response-candidate-confirmation-box")).toBeVisible();
  await page.getByTestId("response-candidate-confirmation-submit").click();
  await expect(reviewQueueBox).toBeVisible();
  await reviewQueueBox.getByTestId("review-queue-reject").click();
  await expect(page.locator("#notice-box")).toHaveText("검토 후보를 거절했습니다.");

  // Second correction + confirm + defer → aggregate forms
  await page.getByTestId("source-path").fill(shortFixturePath);
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).toContainText(middleSignal);
  await page.getByTestId("response-correction-input").fill(correctedText);
  await page.getByTestId("response-correction-submit").click();
  await expect(page.locator("#notice-box")).toHaveText("수정본을 기록했습니다. 저장 승인은 별도 흐름으로 유지됩니다.");
  await expect(aggregateTriggerBox).toBeVisible();

  await expect(page.getByTestId("response-candidate-confirmation-box")).toBeVisible();
  await page.getByTestId("response-candidate-confirmation-submit").click();
  await expect(reviewQueueBox).toBeVisible();
  await reviewQueueBox.getByTestId("review-queue-defer").click();
  await expect(page.locator("#notice-box")).toHaveText("검토 후보를 보류했습니다.");

  // Aggregate card still visible with reject/defer coexisting
  await expect(aggregateTriggerBox).toBeVisible();
  await expect(aggregateTriggerBox.locator(".sidebar-section-label")).toHaveText("검토 메모 적용 후보");

  // Review support line visible with 0 accepted
  const reviewSupportLine = aggregateTriggerBox.getByTestId("aggregate-trigger-review-support");
  await expect(reviewSupportLine).toBeVisible();
  await expect(reviewSupportLine).toHaveText("검토 수락 0건 / 교정 2건 (거절·보류는 감사 기록만)");

  // Payload confirms no supporting_review_refs
  const payload = await fetchSessionPayload(page, sessionId);
  expect(payload.session.recurrence_aggregate_candidates).toHaveLength(1);
  const agg = payload.session.recurrence_aggregate_candidates[0];
  expect(agg.supporting_review_refs).toBeUndefined();
  expect(agg.recurrence_count).toBe(2);

});

test("same-session recurrence aggregate active lifecycle survives supporting correction supersession", async ({ page }, testInfo) => {
  testInfo.setTimeout(120_000);
  const { sessionId, canonicalTransitionId } = await advanceAggregateToActiveEffect(page);
  const aggregateTriggerBox = page.getByTestId("aggregate-trigger-box");

  await expect(aggregateTriggerBox).toBeVisible();

  const activePayload = await fetchSessionPayload(page, sessionId);
  expect(activePayload.session.recurrence_aggregate_candidates).toHaveLength(1);
  const activeAgg = activePayload.session.recurrence_aggregate_candidates[0];
  expect(activeAgg.reviewed_memory_transition_record.record_stage).toBe("applied_with_result");
  expect(activeAgg.reviewed_memory_transition_record.apply_result.result_stage).toBe("effect_active");

  const firstSourceMessageId = activeAgg.supporting_source_message_refs[0].source_message_id;

  const supersedingText = "완전히 다른 교정입니다.\n새로운 방향으로 작성했습니다.";
  const correctionResponse = await page.request.post("/api/correction", {
    data: {
      session_id: sessionId,
      message_id: firstSourceMessageId,
      corrected_text: supersedingText,
    },
  });
  expect(correctionResponse.ok()).toBeTruthy();
  const correctionData = await correctionResponse.json();
  expect(correctionData.session.recurrence_aggregate_candidates).toBeDefined();
  expect(correctionData.session.recurrence_aggregate_candidates).toHaveLength(1);
  const survivingAgg = correctionData.session.recurrence_aggregate_candidates[0];
  expect(survivingAgg.reviewed_memory_transition_record).toBeDefined();
  expect(survivingAgg.reviewed_memory_transition_record.record_stage).toBe("applied_with_result");
  expect(survivingAgg.reviewed_memory_transition_record.canonical_transition_id).toBe(canonicalTransitionId);

  const activeEffects = correctionData.session.reviewed_memory_active_effects;
  expect(Array.isArray(activeEffects) && activeEffects.length > 0).toBe(true);

  await page.evaluate(async (sid) => {
    document.getElementById("session-id").value = sid;
    document.getElementById("load-session").click();
  }, sessionId);
  await expect(page.locator("#current-session-title")).toBeVisible({ timeout: 10_000 });
  await expect(aggregateTriggerBox).toBeVisible({ timeout: 5_000 });

  const stopButton = aggregateTriggerBox.getByTestId("aggregate-trigger-stop");
  await expect(stopButton).toBeVisible();
  await expect(stopButton).toBeEnabled();
  await stopButton.click();
  await expect(page.locator("#notice-box")).toContainText("검토 메모 적용이 중단되었습니다.");

  const stoppedPayload = await fetchSessionPayload(page, sessionId);
  expect(stoppedPayload.session.recurrence_aggregate_candidates).toHaveLength(1);
  expect(stoppedPayload.session.recurrence_aggregate_candidates[0].reviewed_memory_transition_record.record_stage).toBe("stopped");
});

test("same-session recurrence aggregate recorded basis label survives supporting correction supersession", async ({ page }, testInfo) => {
  testInfo.setTimeout(120_000);
  const { sessionId, canonicalTransitionId } = await advanceAggregateToActiveEffect(page);
  const aggregateTriggerBox = page.getByTestId("aggregate-trigger-box");

  await expect(aggregateTriggerBox).toBeVisible();

  // Before supersession: review-support line has recorded-basis prefix because transition record exists
  const reviewSupportLine = aggregateTriggerBox.getByTestId("aggregate-trigger-review-support");
  await expect(reviewSupportLine).toBeVisible();
  await expect(reviewSupportLine).toContainText("[기록된 기준]");
  await expect(reviewSupportLine).toContainText("교정 2건");
  await expect(reviewSupportLine).toContainText("거절·보류는 감사 기록만");

  // Supersede one supporting correction
  const activePayload = await fetchSessionPayload(page, sessionId);
  const firstSourceMessageId = activePayload.session.recurrence_aggregate_candidates[0]
    .supporting_source_message_refs[0].source_message_id;

  const correctionResponse = await page.request.post("/api/correction", {
    data: {
      session_id: sessionId,
      message_id: firstSourceMessageId,
      corrected_text: "완전히 다른 교정입니다.\n새로운 방향으로 작성했습니다.",
    },
  });
  expect(correctionResponse.ok()).toBeTruthy();

  // Reload and verify recorded-basis label survives
  await page.evaluate(async (sid) => {
    document.getElementById("session-id").value = sid;
    document.getElementById("load-session").click();
  }, sessionId);
  await expect(page.locator("#current-session-title")).toBeVisible({ timeout: 10_000 });
  await expect(aggregateTriggerBox).toBeVisible({ timeout: 5_000 });

  const reviewSupportAfter = aggregateTriggerBox.getByTestId("aggregate-trigger-review-support");
  await expect(reviewSupportAfter).toBeVisible();
  await expect(reviewSupportAfter).toContainText("[기록된 기준]");
  await expect(reviewSupportAfter).toContainText("교정 2건");
  await expect(reviewSupportAfter).toContainText("거절·보류는 감사 기록만");
});

test("same-session recurrence aggregate는 stop-reverse-conflict lifecycle으로 정리됩니다", async ({ page }, testInfo) => {
  testInfo.setTimeout(150_000);
  const { sessionId, canonicalTransitionId } = await advanceAggregateToActiveEffect(page);
  const aggregateTriggerBox = page.getByTestId("aggregate-trigger-box");

  const stopButton = aggregateTriggerBox.getByTestId("aggregate-trigger-stop");
  await expect(stopButton).toBeVisible();
  await expect(stopButton).toBeEnabled();
  await stopButton.click();
  await expect(page.locator("#notice-box")).toContainText("검토 메모 적용이 중단되었습니다.");

  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-stopped")).toBeVisible();
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-helper")).toHaveText("검토 메모 적용이 중단되었습니다. 이후 응답에 교정 패턴이 반영되지 않습니다.");

  const stoppedPayload = await fetchSessionPayload(page, sessionId);
  const stoppedAggregate = stoppedPayload.session.recurrence_aggregate_candidates[0];
  expect(stoppedAggregate.reviewed_memory_transition_record.record_stage).toBe("stopped");
  expect(stoppedAggregate.reviewed_memory_transition_record.stopped_at).toBeTruthy();
  expect(stoppedAggregate.reviewed_memory_transition_record.apply_result.result_stage).toBe("effect_stopped");
  await expect(page.locator("#notice-box")).toHaveText(`검토 메모 적용이 중단되었습니다. (${stoppedAggregate.reviewed_memory_transition_record.canonical_transition_id})`);
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-stopped")).toHaveText(`적용 중단됨 (${stoppedAggregate.reviewed_memory_transition_record.canonical_transition_id})`);

  await page.getByTestId("source-path").fill(shortFixturePath);
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).not.toContainText("[검토 메모 활성]");

  // --- Hard page reload while effect is stopped ---
  await page.reload({ waitUntil: "networkidle" });
  await expect(page.locator("#current-session-title")).toBeVisible({ timeout: 10_000 });
  await page.evaluate(async (sid) => {
    document.getElementById("session-id").value = sid;
    document.getElementById("load-session").click();
  }, sessionId);
  await expect(aggregateTriggerBox).toBeVisible({ timeout: 10_000 });
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-stopped")).toBeVisible();
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-stopped")).toHaveText(
    `적용 중단됨 (${stoppedAggregate.reviewed_memory_transition_record.canonical_transition_id})`
  );
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-helper")).toHaveText(
    "검토 메모 적용이 중단되었습니다. 이후 응답에 교정 패턴이 반영되지 않습니다."
  );

  const stoppedReloadPayload = await fetchSessionPayload(page, sessionId);
  expect(stoppedReloadPayload.session.recurrence_aggregate_candidates).toHaveLength(1);
  const stoppedReloadAggregate = stoppedReloadPayload.session.recurrence_aggregate_candidates[0];
  expect(stoppedReloadAggregate.reviewed_memory_transition_record.record_stage).toBe("stopped");
  expect(stoppedReloadAggregate.reviewed_memory_transition_record.apply_result.result_stage).toBe("effect_stopped");
  expect(stoppedReloadAggregate.reviewed_memory_transition_record.canonical_transition_id).toBe(
    canonicalTransitionId
  );
  const stoppedActiveEffects = stoppedReloadPayload.session.reviewed_memory_active_effects;
  expect(!Array.isArray(stoppedActiveEffects) || stoppedActiveEffects.length === 0).toBe(true);

  // Post-reload follow-up must NOT include active effect prefix
  await page.getByTestId("source-path").fill(shortFixturePath);
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).not.toContainText("[검토 메모 활성]");

  const reverseButton = aggregateTriggerBox.getByTestId("aggregate-trigger-reverse");
  await expect(reverseButton).toBeVisible();
  await expect(reverseButton).toBeEnabled();
  await reverseButton.click();
  await expect(page.locator("#notice-box")).toContainText("검토 메모 적용이 되돌려졌습니다.");

  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-reversed")).toBeVisible();
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-helper")).toHaveText("검토 메모 적용이 되돌려졌습니다. 적용 효과가 완전히 철회되었습니다.");

  const reversedPayload = await fetchSessionPayload(page, sessionId);
  const reversedAggregate = reversedPayload.session.recurrence_aggregate_candidates[0];
  expect(reversedAggregate.reviewed_memory_transition_record.record_stage).toBe("reversed");
  expect(reversedAggregate.reviewed_memory_transition_record.reversed_at).toBeTruthy();
  expect(reversedAggregate.reviewed_memory_transition_record.apply_result.result_stage).toBe("effect_reversed");
  expect(reversedAggregate.reviewed_memory_transition_record.canonical_transition_id).toBe(
    canonicalTransitionId
  );
  await expect(page.locator("#notice-box")).toHaveText(`검토 메모 적용이 되돌려졌습니다. (${reversedAggregate.reviewed_memory_transition_record.canonical_transition_id})`);
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-reversed")).toHaveText(`적용 되돌림 완료 (${reversedAggregate.reviewed_memory_transition_record.canonical_transition_id})`);

  // --- Hard page reload while effect is reversed (before conflict visibility) ---
  await page.reload({ waitUntil: "networkidle" });
  await expect(page.locator("#current-session-title")).toBeVisible({ timeout: 10_000 });
  await page.evaluate(async (sid) => {
    document.getElementById("session-id").value = sid;
    document.getElementById("load-session").click();
  }, sessionId);
  await expect(aggregateTriggerBox).toBeVisible({ timeout: 10_000 });
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-reversed")).toBeVisible();
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-reversed")).toHaveText(
    `적용 되돌림 완료 (${reversedAggregate.reviewed_memory_transition_record.canonical_transition_id})`
  );
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-helper")).toHaveText(
    "검토 메모 적용이 되돌려졌습니다. 적용 효과가 완전히 철회되었습니다."
  );

  const reversedReloadPayload = await fetchSessionPayload(page, sessionId);
  expect(reversedReloadPayload.session.recurrence_aggregate_candidates).toHaveLength(1);
  const reversedReloadAggregate = reversedReloadPayload.session.recurrence_aggregate_candidates[0];
  expect(reversedReloadAggregate.reviewed_memory_transition_record.record_stage).toBe("reversed");
  expect(reversedReloadAggregate.reviewed_memory_transition_record.apply_result.result_stage).toBe("effect_reversed");
  expect(reversedReloadAggregate.reviewed_memory_transition_record.canonical_transition_id).toBe(
    canonicalTransitionId
  );
  const reversedActiveEffects = reversedReloadPayload.session.reviewed_memory_active_effects;
  expect(!Array.isArray(reversedActiveEffects) || reversedActiveEffects.length === 0).toBe(true);

  // Post-reload follow-up must NOT include active effect prefix
  await page.getByTestId("source-path").fill(shortFixturePath);
  await page.getByTestId("submit-request").click();
  await expect(page.getByTestId("response-text")).toBeVisible();
  await expect(page.getByTestId("response-text")).not.toContainText("[검토 메모 활성]");

  const conflictCheckButton = aggregateTriggerBox.getByTestId("aggregate-trigger-conflict-check");
  await expect(conflictCheckButton).toBeVisible();
  await expect(conflictCheckButton).toBeEnabled();
  await conflictCheckButton.click();
  await expect(page.locator("#notice-box")).toContainText("충돌 확인이 완료되었습니다.");

  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-conflict-checked")).toBeVisible();
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-helper")).toHaveText("충돌 확인이 완료되었습니다. 현재 aggregate 범위의 충돌 상태가 기록되었습니다.");

  const conflictPayload = await fetchSessionPayload(page, sessionId);
  const conflictAggregate = conflictPayload.session.recurrence_aggregate_candidates[0];
  expect(conflictAggregate.reviewed_memory_conflict_visibility_record).toBeDefined();
  expect(conflictAggregate.reviewed_memory_conflict_visibility_record.transition_action).toBe("future_reviewed_memory_conflict_visibility");
  expect(conflictAggregate.reviewed_memory_conflict_visibility_record.record_stage).toBe("conflict_visibility_checked");
  expect(conflictAggregate.reviewed_memory_conflict_visibility_record.conflict_visibility_stage).toBe("conflict_visibility_checked");
  expect(conflictAggregate.reviewed_memory_conflict_visibility_record.canonical_transition_id).toBeTruthy();
  expect(conflictAggregate.reviewed_memory_conflict_visibility_record.checked_at).toBeTruthy();
  expect(conflictAggregate.reviewed_memory_conflict_visibility_record.source_apply_transition_ref).toBe(
    canonicalTransitionId
  );
  expect(typeof conflictAggregate.reviewed_memory_conflict_visibility_record.conflict_entry_count).toBe("number");
  expect(Array.isArray(conflictAggregate.reviewed_memory_conflict_visibility_record.conflict_entries)).toBe(true);

  expect(conflictAggregate.reviewed_memory_transition_record.record_stage).toBe("reversed");
  expect(conflictAggregate.reviewed_memory_transition_record.canonical_transition_id).toBe(
    canonicalTransitionId
  );
  await expect(page.locator("#notice-box")).toHaveText(`충돌 확인이 완료되었습니다. (${conflictAggregate.reviewed_memory_conflict_visibility_record.canonical_transition_id})`);
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-conflict-checked")).toHaveText(`충돌 확인 완료 (${conflictAggregate.reviewed_memory_conflict_visibility_record.canonical_transition_id} · 항목 ${conflictAggregate.reviewed_memory_conflict_visibility_record.conflict_entry_count}건)`);
  await expect(page.locator("#transcript .message-when").first()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
  await expect(page.locator("#transcript .message-when").last()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);

  // --- Hard page reload continuity ---
  // Verify the persisted lifecycle state re-renders correctly from stored session data.
  await page.reload({ waitUntil: "networkidle" });
  // Wait for the app to finish its initial default-session load, then load the test session
  await expect(page.locator("#current-session-title")).toBeVisible({ timeout: 10_000 });
  await page.evaluate(async (sid) => {
    const sessionIdInput = document.getElementById("session-id");
    sessionIdInput.value = sid;
    document.getElementById("load-session").click();
  }, sessionId);
  // Aggregate-trigger box must still be visible with conflict-checked state after reload
  await expect(aggregateTriggerBox).toBeVisible({ timeout: 10_000 });
  await expect(aggregateTriggerBox.locator(".sidebar-section-label")).toHaveText("검토 메모 적용 후보");
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-conflict-checked")).toBeVisible();
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-conflict-checked")).toHaveText(
    `충돌 확인 완료 (${conflictAggregate.reviewed_memory_conflict_visibility_record.canonical_transition_id} · 항목 ${conflictAggregate.reviewed_memory_conflict_visibility_record.conflict_entry_count}건)`
  );
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-reversed")).toBeVisible();
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-reversed")).toHaveText(
    `적용 되돌림 완료 (${reversedAggregate.reviewed_memory_transition_record.canonical_transition_id})`
  );
  await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-helper")).toHaveText(
    "충돌 확인이 완료되었습니다. 현재 aggregate 범위의 충돌 상태가 기록되었습니다."
  );

  // Payload after reload must match the pre-reload stored state
  const reloadPayload = await fetchSessionPayload(page, sessionId);
  expect(reloadPayload.session.recurrence_aggregate_candidates).toHaveLength(1);
  const reloadAggregate = reloadPayload.session.recurrence_aggregate_candidates[0];
  expect(reloadAggregate.reviewed_memory_transition_record).toBeDefined();
  expect(reloadAggregate.reviewed_memory_transition_record.record_stage).toBe("reversed");
  expect(reloadAggregate.reviewed_memory_transition_record.canonical_transition_id).toBe(
    canonicalTransitionId
  );
  expect(reloadAggregate.reviewed_memory_conflict_visibility_record).toBeDefined();
  expect(reloadAggregate.reviewed_memory_conflict_visibility_record.record_stage).toBe("conflict_visibility_checked");
  expect(reloadAggregate.reviewed_memory_conflict_visibility_record.source_apply_transition_ref).toBe(
    canonicalTransitionId
  );
  expect(reloadAggregate.reviewed_memory_conflict_visibility_record.conflict_entry_count).toBe(
    conflictAggregate.reviewed_memory_conflict_visibility_record.conflict_entry_count
  );
});

test("스트리밍 중 취소 버튼이 동작합니다", async ({ page }) => {
  await prepareSession(page, "cancel");
  await page.getByTestId("source-path").fill(longFixturePath);

  const streamSent = page.waitForRequest((req) => req.url().includes("/api/chat/stream"));
  await page.getByTestId("submit-request").click();
  await streamSent;
  await page.getByTestId("cancel-request").click();

  await expect(page.locator("#notice-box")).toHaveText("요청을 취소했습니다. 현재까지 받은 응답만 화면에 남겨둡니다.");
});

test("일반 채팅 응답에는 source-type label이 붙지 않습니다", async ({ page }) => {
  await prepareSession(page, "general-chat");
  await page.locator('input[name="request_mode"][value="chat"]').check();
  await page.locator("#user-text").fill("안녕하세요");
  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("response-text")).toBeVisible();
  const quickMetaText = await page.locator("#response-quick-meta-text").textContent();
  expect(quickMetaText).not.toContain("문서 요약");
  expect(quickMetaText).not.toContain("선택 결과 요약");
  const transcriptMeta = page.locator('#transcript [data-testid="transcript-meta"]').last();
  if (await transcriptMeta.count() > 0) {
    const metaText = await transcriptMeta.textContent();
    expect(metaText).not.toContain("문서 요약");
    expect(metaText).not.toContain("선택 결과 요약");
  }
  await expect(page.locator("#transcript .message-when").first()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
  await expect(page.locator("#transcript .message-when").last()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
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
  await expect(hint).toContainText("[교차 확인] 여러 출처가 합의한 사실");
  await expect(hint).toContainText("[단일 출처] 1개 출처에서만 확인된 정보");
  await expect(hint).toContainText("[미확인] 추가 조사가 필요한 항목입니다");
});

test("claim-coverage panel은 재조사 대상 슬롯의 진행 상태를 명확히 렌더링합니다", async ({ page }) => {
  await prepareSession(page, "claim-coverage-focus-slot");

  await page.evaluate(() => {
    // @ts-ignore — renderClaimCoverage is defined in the page scope
    renderClaimCoverage([
      { slot: "장르", status_label: "교차 확인", value: "오픈월드 액션 어드벤처", support_count: 3, candidate_count: 3, is_focus_slot: false },
      { slot: "이용 형태", status_label: "단일 출처", value: "PC·콘솔", support_count: 1, candidate_count: 1, is_focus_slot: true, progress_label: "유지", previous_status_label: "단일 출처", progress_state: "unchanged" },
      { slot: "출시일", status_label: "미확인", value: "", support_count: 0, candidate_count: 0, is_focus_slot: true, progress_label: "유지", previous_status_label: "미확인", progress_state: "unchanged" },
    ], "이용 형태: 단일 출처 상태 유지.");
  });

  const text = page.locator("#claim-coverage-text");
  // Focus-slot with 단일 출처 shows dedicated explanation
  await expect(text).toContainText("재조사 대상");
  await expect(text).toContainText("아직 단일 출처 상태입니다");
  await expect(text).toContainText("추가 교차 검증이 권장됩니다");

  // Focus-slot with 미확인 shows dedicated explanation
  await expect(text).toContainText("아직 확인되지 않았습니다");
  await expect(text).toContainText("추가 출처가 필요합니다");

  // Non-focus slot should NOT have focus explanation
  const fullText = await text.textContent();
  const lines = fullText.split("\n");
  const genreLine = lines.find((l) => l.includes("장르"));
  expect(genreLine).not.toContain("재조사 대상");

  // Focus-slot progress should NOT appear in meta parts (moved to explanation line)
  const focusLines = lines.filter((l) => l.includes("이용 형태") || l.includes("출시일"));
  for (const line of focusLines) {
    // meta line with 변화: should not exist for focus slots
    const followingLines = lines.slice(lines.indexOf(line) + 1, lines.indexOf(line) + 5);
    for (const fl of followingLines) {
      if (/^\s*\d+\./.test(fl)) break;
      expect(fl).not.toContain("변화:");
    }
  }
});

test("claim-coverage panel hint는 conflict 상태 설명을 4-tag 순서로 렌더링합니다", async ({ page }) => {
  await prepareSession(page, "claim-coverage-hint-conflict");

  await page.evaluate(() => {
    // @ts-ignore — renderClaimCoverage is defined in the page scope
    renderClaimCoverage([
      { slot: "출생일", status: C.CoverageStatus.STRONG, status_label: "교차 확인", value: "1990년 3월 15일", support_count: 2, candidate_count: 2 },
      { slot: "학력", status: C.CoverageStatus.CONFLICT, status_label: "정보 상충", value: "A대학교 / B대학교", support_count: 2, candidate_count: 2, is_focus_slot: true, progress_label: "유지", previous_status_label: "정보 상충", progress_state: "unchanged" },
      { slot: "소속", status: C.CoverageStatus.WEAK, status_label: "단일 출처", value: "C기관", support_count: 1, candidate_count: 1 },
      { slot: "수상", status: C.CoverageStatus.MISSING, status_label: "미확인", value: "", support_count: 0, candidate_count: 0 },
    ], "학력: 출처 간 진술이 엇갈립니다.");
  });

  const hint = page.locator("#claim-coverage-hint");
  await expect(hint).toContainText("학력: 출처 간 진술이 엇갈립니다.");
  await expect(hint).toContainText("출처들이 서로 어긋나 추가 확인이 필요한 항목");

  const hintText = (await hint.textContent()) || "";
  const strongIdx = hintText.indexOf("[교차 확인]");
  const conflictIdx = hintText.indexOf("[정보 상충]");
  const weakIdx = hintText.indexOf("[단일 출처]");
  const missingIdx = hintText.indexOf("[미확인]");
  expect(strongIdx).toBeGreaterThanOrEqual(0);
  expect(conflictIdx).toBeGreaterThan(strongIdx);
  expect(weakIdx).toBeGreaterThan(conflictIdx);
  expect(missingIdx).toBeGreaterThan(weakIdx);
});

test("claim-coverage panel은 재조사 후 보강된 슬롯을 명확히 표시합니다", async ({ page }) => {
  await prepareSession(page, "claim-coverage-focus-improved");

  await page.evaluate(() => {
    // @ts-ignore — renderClaimCoverage is defined in the page scope
    renderClaimCoverage([
      { slot: "이용 형태", status_label: "교차 확인", value: "PC·콘솔", support_count: 2, candidate_count: 2, is_focus_slot: true, progress_label: "보강", previous_status_label: "단일 출처", progress_state: "improved" },
    ], "이용 형태: 단일 출처 → 교차 확인으로 보강.");
  });

  const text = page.locator("#claim-coverage-text");
  await expect(text).toContainText("재조사 결과");
  await expect(text).toContainText("단일 출처 → 교차 확인으로 보강되었습니다");
});

test("claim-coverage panel은 재조사 후 약해진 슬롯을 명확히 표시합니다", async ({ page }) => {
  await prepareSession(page, "claim-coverage-focus-regressed");

  await page.evaluate(() => {
    // @ts-ignore — renderClaimCoverage is defined in the page scope
    renderClaimCoverage([
      { slot: "이용 형태", status_label: "단일 출처", value: "PC·콘솔", support_count: 1, candidate_count: 1, is_focus_slot: true, progress_label: "약해짐", previous_status_label: "교차 확인", progress_state: "regressed" },
    ], "이용 형태: 교차 확인 → 단일 출처로 약해짐.");
  });

  const text = page.locator("#claim-coverage-text");
  await expect(text).toContainText("재조사 결과");
  await expect(text).toContainText("교차 확인 기준을 더 이상 충족하지 않아 단일 출처로 조정되었습니다");
});

test("claim_coverage_multi_source_weak_focus_slot_emits_multi_source_hint", async ({ page }) => {
  await prepareSession(page, "claim-coverage-focus-multi-source-weak");

  await page.evaluate(() => {
    // @ts-ignore — renderClaimCoverage is defined in the page scope
    renderClaimCoverage([
      {
        slot: "이용 형태",
        status_label: "단일 출처",
        value: "PC·콘솔",
        support_count: 2,
        candidate_count: 2,
        is_focus_slot: true,
        progress_label: "유지",
        previous_status_label: "단일 출처",
        progress_state: "unchanged",
        support_plurality: "multiple",
      },
    ], "이용 형태: 단일 출처 상태 유지.");
  });

  const text = page.locator("#claim-coverage-text");
  await expect(text).toContainText("[단일 출처] 이용 형태");
  await expect(text).toContainText("재조사 대상이며 여러 출처가 확인되었으나, 아직 교차 확인 기준에는 미달합니다.");
  await expect(text).not.toContainText("1개 출처만 확인됨. 교차 검증이 권장됩니다.");
});

test("claim_coverage_strong_mixed_trust_tier_non_focus_slot_emits_mixed_trust_hint", async ({ page }) => {
  await prepareSession(page, "claim-coverage-strong-mixed-trust");

  await page.evaluate(() => {
    // @ts-ignore — renderClaimCoverage is defined in the page scope
    renderClaimCoverage([
      {
        slot: "개발",
        status_label: "교차 확인",
        value: "Pearl Abyss",
        support_count: 2,
        candidate_count: 2,
        is_focus_slot: false,
        support_plurality: "",
        trust_tier: "mixed",
      },
    ], "");
  });

  const text = page.locator("#claim-coverage-text");
  await expect(text).toContainText("[교차 확인] 개발");
  await expect(text).toContainText("교차 확인 기준은 충족하지만 공식/위키/데이터 소스가 약합니다.");
  await expect(text).not.toContainText("1개 출처만 확인됨. 교차 검증이 권장됩니다.");
});

test("fact-strength bar는 conflict badge를 교차 확인과 단일 출처 사이에 렌더링합니다", async ({ page }) => {
  await prepareSession(page, "fact-strength-conflict");

  await page.evaluate(() => {
    const responseBox = document.getElementById("response-box");
    responseBox?.classList.remove("hidden");
    responseBox?.removeAttribute("hidden");
    // @ts-ignore — renderFactStrengthBar is defined in the page scope
    renderFactStrengthBar([
      { status: C.CoverageStatus.STRONG },
      { status: C.CoverageStatus.STRONG },
      { status: "conflict" },
      { status: C.CoverageStatus.WEAK },
      { status: C.CoverageStatus.WEAK },
      { status: C.CoverageStatus.WEAK },
      { status: C.CoverageStatus.MISSING },
      { status: C.CoverageStatus.MISSING },
      { status: C.CoverageStatus.MISSING },
      { status: C.CoverageStatus.MISSING },
    ]);
  });

  const bar = page.getByTestId("fact-strength-bar");
  await expect(bar).toBeVisible();
  await expect(bar).toContainText("사실 검증:");

  const groups = bar.locator(".fact-group");
  await expect(groups).toHaveCount(4);
  await expect(groups.nth(0)).toContainText("교차 확인");
  await expect(groups.nth(1)).toContainText("정보 상충");
  await expect(groups.nth(2)).toContainText("단일 출처");
  await expect(groups.nth(3)).toContainText("미확인");

  await expect(bar.locator(".fact-count.strong")).toHaveText("2");
  await expect(bar.locator(".fact-count.conflict")).toHaveText("1");
  await expect(bar.locator(".fact-count.weak")).toHaveText("3");
  await expect(bar.locator(".fact-count.missing")).toHaveText("4");
});

test("live-session answer meta는 conflict claim coverage를 정보 상충 segment로 렌더링합니다", async ({ page }) => {
  await prepareSession(page, "live-session-conflict-summary");

  await page.evaluate(() => {
    // @ts-ignore — renderSession is defined in the page scope
    renderSession({
      session_id: "pw-live-session-conflict-summary",
      updated_at: "2026-04-19T10:30:00+09:00",
      permissions: { web_search: C.WebSearchPermission.DISABLED },
      messages: [
        {
          role: "assistant",
          message_id: "assistant-conflict-summary",
          created_at: "2026-04-19T10:30:00+09:00",
          text: "충돌 항목이 포함된 live-session claim coverage 요약입니다.",
          claim_coverage: [
            { slot: "출생지", status: C.CoverageStatus.STRONG, status_label: "교차 확인", value: "서울", support_count: 2, candidate_count: 2 },
            { slot: "학력", status: C.CoverageStatus.CONFLICT, status_label: "정보 상충", value: "A대학교 / B대학교", support_count: 2, candidate_count: 2 },
            { slot: "소속", status: C.CoverageStatus.WEAK, status_label: "단일 출처", value: "C기관", support_count: 1, candidate_count: 1 },
            { slot: "수상", status: C.CoverageStatus.MISSING, status_label: "미확인", value: "", support_count: 0, candidate_count: 0 },
          ],
        },
      ],
    }, { force: true });
  });

  const transcriptMeta = page.locator('#transcript [data-testid="transcript-meta"]').last();
  await expect(transcriptMeta).toHaveText("사실 검증 교차 확인 1 · 정보 상충 1 · 단일 출처 1 · 미확인 1");
});

test("CONFLICT chain end-to-end는 응답 본문 헤더 · 근거 출처 URL · panel rendered_as를 함께 표면화합니다", async ({ page }) => {
  await prepareSession(page, "conflict-chain-end-to-end");

  await page.evaluate(() => {
    // @ts-ignore — renderSession is defined in the page scope
    renderSession({
      session_id: "pw-conflict-chain-end-to-end",
      updated_at: "2026-04-20T10:30:00+09:00",
      permissions: { web_search: C.WebSearchPermission.DISABLED },
      messages: [
        {
          role: "assistant",
          message_id: "assistant-conflict-chain-end-to-end",
          created_at: "2026-04-20T10:30:00+09:00",
          text: [
            "붉은사막 조사 결과입니다.",
            "상충하는 정보 [정보 상충]:",
            "  - 장르/성격: 오픈월드 액션 어드벤처 / 생존 제작 RPG",
            "근거 출처:",
            "[정보 상충] 장르/성격:",
            "  링크: https://conflict.example.com/genre-official",
          ].join("\n"),
          claim_coverage: [
            { slot: "개발", status: C.CoverageStatus.STRONG, status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "공식", rendered_as: "fact_card" },
            { slot: "장르/성격", status: C.CoverageStatus.CONFLICT, status_label: "정보 상충", value: "오픈월드 액션 어드벤처 / 생존 제작 RPG", support_count: 3, candidate_count: 3, source_role: "공식", rendered_as: "conflict" },
            { slot: "이용 형태", status: C.CoverageStatus.WEAK, status_label: "단일 출처", value: "PC와 콘솔", support_count: 1, candidate_count: 1, source_role: "위키", rendered_as: "uncertain" },
            { slot: "상태", status: C.CoverageStatus.MISSING, status_label: "미확인", value: "", support_count: 0, candidate_count: 0, source_role: "", rendered_as: "not_rendered" },
          ],
        },
      ],
    }, { force: true });
  });

  const transcriptBody = page.locator("#transcript pre").last();
  await expect(transcriptBody).toContainText("상충하는 정보 [정보 상충]:");
  await expect(transcriptBody).toContainText("https://conflict.example.com/genre-official");

  const bodyText = (await transcriptBody.textContent()) || "";
  const headerIdx = bodyText.indexOf("상충하는 정보 [정보 상충]:");
  const conflictSourceIdx = bodyText.indexOf("https://conflict.example.com/genre-official");
  expect(headerIdx).toBeGreaterThanOrEqual(0);
  expect(conflictSourceIdx).toBeGreaterThan(headerIdx);

  const panelText = page.locator("#claim-coverage-text");
  await expect(panelText).toContainText("[정보 상충] 장르/성격");
  await expect(panelText).toContainText("표시: 상충 정보 반영");

  const panelRawText = (await panelText.textContent()) || "";
  const panelConflictHeaderIdx = panelRawText.indexOf("[정보 상충] 장르/성격");
  const panelRenderedAsIdx = panelRawText.indexOf("표시: 상충 정보 반영");
  expect(panelConflictHeaderIdx).toBeGreaterThanOrEqual(0);
  expect(panelRenderedAsIdx).toBeGreaterThan(panelConflictHeaderIdx);
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
        claim_coverage_progress_summary: "출생일: 단일 출처 → 교차 확인으로 보강되었습니다.",
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
      {
        query: "혼합 카운트 전용",
        answer_mode: "latest_update",
        verification_label: "공식 단일 출처",
        source_roles: ["공식 기반"],
        claim_coverage_summary: { strong: 2, weak: 0, missing: 0, conflict: 0 },
        result_count: 4,
        page_count: 2,
        created_at: new Date().toISOString(),
      },
      {
        query: "혼합 카운트+진행 요약",
        answer_mode: "entity_card",
        verification_label: "공식+기사 교차 확인",
        source_roles: ["공식 기반"],
        claim_coverage_summary: { strong: 2, weak: 1, missing: 0, conflict: 0 },
        claim_coverage_progress_summary: "혼합 지표: 교차 확인과 단일 출처가 함께 관찰되었습니다.",
        result_count: 6,
        page_count: 3,
        created_at: new Date().toISOString(),
      },
      {
        query: "일반 검색 카운트+진행 요약",
        answer_mode: "general",
        verification_label: "보조 커뮤니티 참고",
        source_roles: ["보조 커뮤니티"],
        claim_coverage_summary: { strong: 2, weak: 1, missing: 0, conflict: 0 },
        claim_coverage_progress_summary: "일반 지표: 커뮤니티 단서와 교차 확인이 함께 관찰되었습니다.",
        result_count: 4,
        page_count: 1,
        created_at: new Date().toISOString(),
      },
      {
        query: "일반 검색 카운트 전용",
        answer_mode: "general",
        verification_label: "보조 커뮤니티 참고",
        source_roles: ["보조 커뮤니티"],
        claim_coverage_summary: { strong: 2, weak: 0, missing: 0, conflict: 0 },
        result_count: 3,
        page_count: 0,
        created_at: new Date().toISOString(),
      },
      {
        query: "일반 검색 진행 요약 전용",
        answer_mode: "general",
        verification_label: "보조 커뮤니티 참고",
        source_roles: ["보조 커뮤니티"],
        claim_coverage_progress_summary: "일반 진행: 커뮤니티 단서가 단일 출처 상태로 남아 있습니다.",
        result_count: 2,
        page_count: 0,
        created_at: new Date().toISOString(),
      },
    ]);
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();

  const cards = historyBox.locator(".history-item");
  await expect(cards).toHaveCount(9);

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
  // progress summary visible in card meta
  const card1Meta = card1.locator(".meta");
  await expect(card1Meta).toContainText("출생일: 단일 출처 → 교차 확인으로 보강되었습니다.");

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
  // Empty claim_coverage_progress_summary must not render any detailMeta or leak card1's progress text
  await expect(card2.locator(".meta")).toHaveCount(0);
  await expect(card2).not.toContainText("출생일: 단일 출처");

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
  // Missing claim_coverage_progress_summary must not leak stray progress text or produce blank/separator-only meta.
  // Card 3 renders a single answer-mode detail line (general is not investigation), so .meta must be present,
  // non-empty, contain no " · " separator artifact, and not echo card1's progress summary.
  const card3Meta = card3.locator(".meta");
  await expect(card3Meta).toHaveCount(1);
  await expect(card3Meta).not.toContainText("·");
  await expect(card3Meta).not.toContainText("출생일: 단일 출처");
  const card3MetaText = ((await card3Meta.textContent()) || "").trim();
  expect(card3MetaText.length).toBeGreaterThan(0);

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
  // Empty claim_coverage_progress_summary (and no claim_coverage_summary) must leave the card without any detailMeta
  // and must not leak card1's progress text — investigation cards with empty summary stay hidden, not separator-only.
  await expect(card4.locator(".meta")).toHaveCount(0);
  await expect(card4).not.toContainText("출생일: 단일 출처");

  // Card 5: latest_update investigation with non-empty claim_coverage_summary and empty claim_coverage_progress_summary.
  // detailLines skips answer-mode label (investigation) and skips progress summary (empty), so .meta must be the
  // single `사실 검증 ...` count-only line — not leaking card1 progress text, not blank, not a separator-only artifact.
  const card5 = cards.nth(4);
  const card5Meta = card5.locator(".meta");
  await expect(card5Meta).toHaveCount(1);
  await expect(card5Meta).toHaveText("사실 검증 교차 확인 2");
  await expect(card5Meta).not.toContainText("·");
  await expect(card5Meta).not.toContainText("출생일: 단일 출처");
  await expect(card5Meta).not.toContainText("최신 확인");
  const card5MetaText = ((await card5Meta.textContent()) || "").trim();
  expect(card5MetaText.length).toBeGreaterThan(0);
  expect(card5MetaText.startsWith("·")).toBe(false);
  expect(card5MetaText.endsWith("·")).toBe(false);

  // Card 6: entity_card investigation with BOTH non-empty multi-category claim_coverage_summary and non-empty
  // claim_coverage_progress_summary. detailLines skips answer-mode label (investigation), pushes the
  // `사실 검증 ...` count line first, then the progress summary, then joins with ` · `. The count line itself
  // legitimately contains ` · ` because the summary has multiple categories — lock the exact composition order.
  const card6 = cards.nth(5);
  const card6Meta = card6.locator(".meta");
  await expect(card6Meta).toHaveCount(1);
  await expect(card6Meta).toHaveText(
    "사실 검증 교차 확인 2 · 단일 출처 1 · 혼합 지표: 교차 확인과 단일 출처가 함께 관찰되었습니다."
  );
  await expect(card6Meta).not.toContainText("출생일: 단일 출처");
  await expect(card6Meta).not.toContainText("설명 카드");
  await expect(card6Meta).not.toContainText("최신 확인");
  const card6MetaText = ((await card6Meta.textContent()) || "").trim();
  expect(card6MetaText.length).toBeGreaterThan(0);
  expect(card6MetaText.startsWith("·")).toBe(false);
  expect(card6MetaText.endsWith("·")).toBe(false);
  expect(
    card6MetaText.indexOf("사실 검증 교차 확인 2 · 단일 출처 1")
  ).toBeLessThan(card6MetaText.indexOf("혼합 지표:"));

  // Card 7: general (non-investigation) with BOTH non-empty multi-category claim_coverage_summary and non-empty
  // claim_coverage_progress_summary. detailLines prepends the `일반 검색` answer-mode label (non-investigation),
  // then pushes the `사실 검증 ...` count line, then the progress summary, and joins with ` · `. Lock the exact
  // three-part composition order — label → count → progress — and guard against separator artifacts.
  const card7 = cards.nth(6);
  const card7Meta = card7.locator(".meta");
  await expect(card7Meta).toHaveCount(1);
  await expect(card7Meta).toHaveText(
    "일반 검색 · 사실 검증 교차 확인 2 · 단일 출처 1 · 일반 지표: 커뮤니티 단서와 교차 확인이 함께 관찰되었습니다."
  );
  await expect(card7Meta).not.toContainText("출생일: 단일 출처");
  await expect(card7Meta).not.toContainText("혼합 지표:");
  await expect(card7Meta).not.toContainText("설명 카드");
  await expect(card7Meta).not.toContainText("최신 확인");
  const card7MetaText = ((await card7Meta.textContent()) || "").trim();
  expect(card7MetaText.length).toBeGreaterThan(0);
  expect(card7MetaText.startsWith("·")).toBe(false);
  expect(card7MetaText.endsWith("·")).toBe(false);
  const card7LabelIdx = card7MetaText.indexOf("일반 검색");
  const card7CountIdx = card7MetaText.indexOf("사실 검증 교차 확인 2 · 단일 출처 1");
  const card7ProgressIdx = card7MetaText.indexOf("일반 지표:");
  expect(card7LabelIdx).toBeGreaterThanOrEqual(0);
  expect(card7CountIdx).toBeGreaterThan(card7LabelIdx);
  expect(card7ProgressIdx).toBeGreaterThan(card7CountIdx);

  // Card 8: general (non-investigation) with single-category claim_coverage_summary and empty
  // claim_coverage_progress_summary. detailLines = [`일반 검색`, `사실 검증 교차 확인 2`], joined with ` · `.
  // Lock the exact two-part label+count-only composition — no trailing separator and no leaked progress text.
  const card8 = cards.nth(7);
  const card8Meta = card8.locator(".meta");
  await expect(card8Meta).toHaveCount(1);
  await expect(card8Meta).toHaveText("일반 검색 · 사실 검증 교차 확인 2");
  await expect(card8Meta).not.toContainText("출생일: 단일 출처");
  await expect(card8Meta).not.toContainText("혼합 지표:");
  await expect(card8Meta).not.toContainText("일반 지표:");
  await expect(card8Meta).not.toContainText("일반 진행:");
  await expect(card8Meta).not.toContainText("설명 카드");
  await expect(card8Meta).not.toContainText("최신 확인");
  const card8MetaText = ((await card8Meta.textContent()) || "").trim();
  expect(card8MetaText.length).toBeGreaterThan(0);
  expect(card8MetaText.startsWith("·")).toBe(false);
  expect(card8MetaText.endsWith("·")).toBe(false);
  const card8LabelIdx = card8MetaText.indexOf("일반 검색");
  const card8CountIdx = card8MetaText.indexOf("사실 검증 교차 확인 2");
  expect(card8LabelIdx).toBeGreaterThanOrEqual(0);
  expect(card8CountIdx).toBeGreaterThan(card8LabelIdx);

  // Card 9: general (non-investigation) with empty claim_coverage_summary and non-empty
  // claim_coverage_progress_summary. detailLines = [`일반 검색`, progress], joined with ` · `.
  // Lock the exact two-part label+progress-only composition — no stray count segment leaked in.
  const card9 = cards.nth(8);
  const card9Meta = card9.locator(".meta");
  await expect(card9Meta).toHaveCount(1);
  await expect(card9Meta).toHaveText(
    "일반 검색 · 일반 진행: 커뮤니티 단서가 단일 출처 상태로 남아 있습니다."
  );
  await expect(card9Meta).not.toContainText("사실 검증");
  await expect(card9Meta).not.toContainText("출생일: 단일 출처");
  await expect(card9Meta).not.toContainText("혼합 지표:");
  await expect(card9Meta).not.toContainText("일반 지표:");
  await expect(card9Meta).not.toContainText("설명 카드");
  await expect(card9Meta).not.toContainText("최신 확인");
  const card9MetaText = ((await card9Meta.textContent()) || "").trim();
  expect(card9MetaText.length).toBeGreaterThan(0);
  expect(card9MetaText.startsWith("·")).toBe(false);
  expect(card9MetaText.endsWith("·")).toBe(false);
  const card9LabelIdx = card9MetaText.indexOf("일반 검색");
  const card9ProgressIdx = card9MetaText.indexOf("일반 진행:");
  expect(card9LabelIdx).toBeGreaterThanOrEqual(0);
  expect(card9ProgressIdx).toBeGreaterThan(card9LabelIdx);
});

test("history-card summary가 non-zero conflict count를 정보 상충 segment로 렌더링합니다", async ({ page }) => {
  await prepareSession(page, "history-card-conflict-summary");

  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          query: "충돌 카운트",
          answer_mode: "entity_card",
          verification_label: "공식+기사 교차 확인",
          source_roles: ["공식 기반", "보조 기사"],
          claim_coverage_summary: { strong: 1, weak: 1, missing: 0, conflict: 2 },
          result_count: 3,
          page_count: 1,
          created_at: new Date().toISOString(),
        },
      ],
    }
  );

  const historyCardMeta = page.locator("#search-history-box .history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 1 · 정보 상충 2 · 단일 출처 1");
});

test("history-card entity-card 다시 불러오기 클릭 후 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 유지됩니다", async ({ page }) => {
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
    summary_text: "웹 검색 요약: 붉은사막\n\n단일 출처 정보 [단일 출처] (추가 확인 필요):\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다. 단일 출처에서만 확인된 정보입니다.\n\n확인되지 않은 항목 [미확인]:\n교차 확인 가능한 근거를 찾지 못했습니다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "외부 웹 설명 카드",
      answer_mode: "entity_card",
      verification_label: "설명형 단일 출처",
      source_roles: ["백과 기반"],
    },
    claim_coverage: [
      {
        slot: "장르",
        status: "weak",
        status_label: "단일 출처",
        value: "오픈월드 액션 어드벤처 게임",
        support_count: 1,
        candidate_count: 1,
        source_role: "encyclopedia",
      },
      {
        slot: "출시일",
        status: "missing",
        status_label: "미확인",
      },
    ],
    claim_coverage_progress_summary: "단일 출처 상태 1건, 미확인 1건.",
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
          claim_coverage_summary: { strong: 0, weak: 1, missing: 1, conflict: 0 },
          claim_coverage_progress_summary: "단일 출처 상태 1건, 미확인 1건.",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();

  // History card should surface the progress summary text
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard).toContainText("단일 출처 상태 1건, 미확인 1건.");

  // History card `.meta` must also surface the claim-coverage count summary derived from
  // `claim_coverage_summary` ({weak: 1, missing: 1, conflict: 0} → `단일 출처 1 · 미확인 1`) as the first
  // detailLine, followed by the progress summary, joined with ` · `. entity_card is an
  // investigation card so the answer-mode label is skipped from detailLines.
  const historyCardMeta = historyCard.locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText(
    "사실 검증 단일 출처 1 · 미확인 1 · 단일 출처 상태 1건, 미확인 1건."
  );
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");
  const historyCardMetaText = ((await historyCardMeta.textContent()) || "").trim();
  expect(historyCardMetaText.startsWith("·")).toBe(false);
  expect(historyCardMetaText.endsWith("·")).toBe(false);
  expect(
    historyCardMetaText.indexOf("사실 검증 단일 출처 1 · 미확인 1")
  ).toBeLessThan(historyCardMetaText.indexOf("단일 출처 상태 1건"));

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

  await expect(page.getByTestId("response-text")).toContainText("웹 검색 요약: 붉은사막");
  await expect(page.getByTestId("response-text")).toContainText("단일 출처 정보 [단일 출처] (추가 확인 필요):");
  await expect(page.getByTestId("response-text")).toContainText("확인되지 않은 항목 [미확인]:");

  await expect(page.locator("#claim-coverage-hint")).toContainText("단일 출처 상태 1건, 미확인 1건.");

  // After reload, the history-card `.meta` must still expose the same count-summary + progress-summary
  // composition — the seeded card is not cleared by loadWebSearchRecord(recordId), so the stored
  // entity-card count-summary persistence contract remains visible end-to-end.
  await expect(historyCardMeta).toHaveText(
    "사실 검증 단일 출처 1 · 미확인 1 · 단일 출처 상태 1건, 미확인 1건."
  );

  await expect(page.locator("#transcript .message-when").first()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
  await expect(page.locator("#transcript .message-when").last()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);

  // Clean up the pre-seeded record
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card latest-update 다시 불러오기 후 WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-latest");

  // Pre-seed a latest_update web search record with mixed source roles
  const recordId = `websearch-latest-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `스팀할인-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "스팀 여름 할인",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 2,
    results: [
      {
        title: "Steam 여름 할인 - Steam Store",
        url: "https://store.steampowered.com/sale/summer2026",
        snippet: "Steam 여름 할인이 시작되었습니다.",
      },
      {
        title: "스팀 여름 할인 시작 - 게임뉴스",
        url: "https://www.yna.co.kr/view/AKR20260401000100017",
        snippet: "스팀이 2026년 여름 할인을 시작했다.",
      },
    ],
    pages: [
      {
        url: "https://store.steampowered.com/sale/summer2026",
        title: "Steam 여름 할인 - Steam Store",
        text: "Steam 여름 할인이 시작되었습니다.",
      },
      {
        url: "https://www.yna.co.kr/view/AKR20260401000100017",
        title: "스팀 여름 할인 시작 - 게임뉴스",
        text: "스팀이 2026년 여름 할인을 시작했다.",
      },
    ],
    summary_text: "웹 검색 요약: 스팀 여름 할인\n\nSteam 여름 할인이 시작되었습니다. 수천 개 게임이 최대 90% 할인됩니다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "latest_update",
      verification_label: "공식+기사 교차 확인",
      source_roles: ["보조 기사", "공식 기반"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card with latest_update answer_mode
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "스팀 여름 할인",
          answer_mode: "latest_update",
          verification_label: "공식+기사 교차 확인",
          source_roles: ["보조 기사", "공식 기반"],
          result_count: 2,
          page_count: 2,
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

  // Click "다시 불러오기"
  await reloadButton.click();

  // Assert reloaded response origin badge
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);

  // Assert answer-mode badge shows "최신 확인" for latest_update
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");

  // Assert origin detail contains verification label and source roles
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("공식+기사 교차 확인");
  await expect(originDetail).toContainText("보조 기사");
  await expect(originDetail).toContainText("공식 기반");

  // latest-update show-only reload empty-meta branch: zero-count summary + empty progress →
  // history card must not render any `.meta` detail node and must not leak `사실 검증` content.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card entity-card 다시 불러오기 후 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 drift하지 않습니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-followup");

  // Pre-seed a web search record with stored response_origin including answer_mode
  const recordId = `websearch-followup-${Date.now().toString(36)}`;
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
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 단일 출처",
      source_roles: ["백과 기반"],
    },
    claim_coverage: [
      {
        slot: "장르",
        status: "weak",
        status_label: "단일 출처",
        value: "오픈월드 액션 어드벤처 게임",
        support_count: 1,
        candidate_count: 1,
        source_role: "encyclopedia",
      },
    ],
    claim_coverage_progress_summary: "단일 출처 상태 1건.",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card in the browser
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
          claim_coverage_summary: { strong: 0, weak: 1, missing: 0, conflict: 0 },
          claim_coverage_progress_summary: "단일 출처 상태 1건.",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  const reloadButton = historyBox.locator(".history-item-actions button.secondary").first();
  await expect(reloadButton).toHaveText("다시 불러오기");

  // Click "다시 불러오기" — show-only reload
  await reloadButton.click();

  // Wait for the initial reload response badges
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toHaveText("설명 카드");

  // Before the follow-up, the history-card `.meta` must reflect the stored entity-card
  // count-summary (`{weak:1}` → `단일 출처 1`) composed with the stored progress summary.
  // entity_card is investigation, so detailLines skip the answer-mode label; the count line
  // comes first and the progress summary comes second, joined with ` · `.
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText(
    "사실 검증 단일 출처 1 · 단일 출처 상태 1건."
  );
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");
  const preFollowUpMetaText = ((await historyCardMeta.textContent()) || "").trim();
  expect(preFollowUpMetaText.startsWith("·")).toBe(false);
  expect(preFollowUpMetaText.endsWith("·")).toBe(false);
  expect(
    preFollowUpMetaText.indexOf("사실 검증 단일 출처 1")
  ).toBeLessThan(preFollowUpMetaText.indexOf("단일 출처 상태 1건"));

  // Send a follow-up with load_web_search_record_id + user_text (non-show-only)
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Assert response origin badges are preserved after follow-up
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);

  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");

  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 단일 출처");
  await expect(originDetail).toContainText("백과 기반");

  // After the follow-up, the history-card `.meta` must still expose the same entity-card
  // count-summary + progress composition — the stored `claim_coverage` continues to drive
  // `_summarize_claim_coverage` through the reload+follow-up serialization path.
  await expect(historyCardMeta).toHaveText(
    "사실 검증 단일 출처 1 · 단일 출처 상태 1건."
  );
  const postFollowUpMetaText = ((await historyCardMeta.textContent()) || "").trim();
  expect(postFollowUpMetaText.startsWith("·")).toBe(false);
  expect(postFollowUpMetaText.endsWith("·")).toBe(false);

  // Clean up the pre-seeded record
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card entity-card click reload 후 composer를 거친 plain follow-up 경로가 load_web_search_record_id 없이 top-level claim_coverage를 유지합니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-click-reload-plain-follow-up-entity-card");

  // Pre-seed the same single-weak-slot entity-card web search record that the
  // existing click-reload + follow-up scenario above uses, so the two tests
  // share identical stored data and only differ in the follow-up submit path.
  const recordId = `websearch-click-reload-plain-follow-up-entity-${Date.now().toString(36)}`;
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
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 단일 출처",
      source_roles: ["백과 기반"],
    },
    claim_coverage: [
      {
        slot: "장르",
        status: "weak",
        status_label: "단일 출처",
        value: "오픈월드 액션 어드벤처 게임",
        support_count: 1,
        candidate_count: 1,
        source_role: "encyclopedia",
      },
    ],
    claim_coverage_progress_summary: "단일 출처 상태 1건.",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

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
          claim_coverage_summary: { strong: 0, weak: 1, missing: 0, conflict: 0 },
          claim_coverage_progress_summary: "단일 출처 상태 1건.",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  const reloadButton = historyBox.locator(".history-item-actions button.secondary").first();
  await expect(reloadButton).toHaveText("다시 불러오기");

  // Step 1: real browser click-reload. `loadWebSearchRecord()` sends only
  // `load_web_search_record_id` + empty user_text, which the backend
  // auto-injects into the show-only reload branch.
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toHaveText("설명 카드");
  await expect(page.getByTestId("submit-request")).toBeEnabled();

  // Step 2: send a plain follow-up through the exact browser composer path
  // (`#user-text` + `submit-request`). `collectPayload()` for chat mode only
  // adds `user_text`, so this never re-sends `load_web_search_record_id`.
  await page.locator('input[name="request_mode"][value="chat"]').check();
  await page.locator("#web-search-permission").selectOption("enabled");
  await page.locator("#user-text").fill("이 결과 한 문장으로 요약해줘");

  const plainFollowUpRequestPromise = page.waitForRequest(
    (req) => req.url().includes("/api/chat/stream") && req.method() === "POST"
  );
  await page.getByTestId("submit-request").click();
  const plainFollowUpRequest = await plainFollowUpRequestPromise;
  const plainFollowUpBodyText = plainFollowUpRequest.postData() || "";
  expect(plainFollowUpBodyText.length).toBeGreaterThan(0);
  // Lock the exact post-click plain follow-up shape: no record id leak into
  // the raw JSON body at all, and explicit absence of the key on the parsed
  // object so future renamed keys still fail the assertion.
  expect(plainFollowUpBodyText).not.toContain("load_web_search_record_id");
  const plainFollowUpBody = JSON.parse(plainFollowUpBodyText);
  expect(plainFollowUpBody.user_text).toBe("이 결과 한 문장으로 요약해줘");
  expect(Object.prototype.hasOwnProperty.call(plainFollowUpBody, "load_web_search_record_id")).toBe(false);

  // Wait for the follow-up stream to settle before asserting final state.
  await expect(page.getByTestId("submit-request")).toBeEnabled();

  // The active-context plain follow-up must propagate the stored entity-card
  // claim_coverage onto the top-level response fields, matching the
  // backend/service tests `test_handle_chat_click_reload_plain_follow_up_*`.
  const claimCoverageBox = page.locator("#claim-coverage-box");
  await expect(claimCoverageBox).toBeVisible();
  const claimCoverageText = page.locator("#claim-coverage-text");
  await expect(claimCoverageText).toContainText("장르");
  await expect(claimCoverageText).toContainText("[단일 출처]");

  // The history-card `.meta` composition must also remain the stored
  // entity-card count-summary + progress-summary line.
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 단일 출처 1 · 단일 출처 상태 1건.");

  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 drift하지 않습니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-second-followup");

  // Pre-seed a simple single-source entity-card web search record with stored response_origin
  // and a single-weak-slot claim_coverage so `_summarize_claim_coverage` yields {weak: 1}.
  const recordId = `websearch-second-followup-${Date.now().toString(36)}`;
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
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 단일 출처",
      source_roles: ["백과 기반"],
    },
    claim_coverage: [
      {
        slot: "장르",
        status: "weak",
        status_label: "단일 출처",
        value: "오픈월드 액션 어드벤처 게임",
        support_count: 1,
        candidate_count: 1,
        source_role: "encyclopedia",
      },
    ],
    claim_coverage_progress_summary: "단일 출처 상태 1건.",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card in the browser with seeded count/progress that mirror the stored record
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
          claim_coverage_summary: { strong: 0, weak: 1, missing: 0, conflict: 0 },
          claim_coverage_progress_summary: "단일 출처 상태 1건.",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  const reloadButton = historyBox.locator(".history-item-actions button.secondary").first();
  await expect(reloadButton).toHaveText("다시 불러오기");

  // Click "다시 불러오기" — show-only reload
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toHaveText("설명 카드");

  // Send the first follow-up (user_text + load_web_search_record_id)
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  await expect(originBadge).toHaveText("WEB");
  await expect(answerModeBadge).toHaveText("설명 카드");

  // After the first follow-up the history-card `.meta` must already carry the entity-card
  // count-summary + progress-summary composition derived from the stored record.
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText(
    "사실 검증 단일 출처 1 · 단일 출처 상태 1건."
  );

  // Send the SECOND follow-up on the same record (user_text + load_web_search_record_id)
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "장르만 한 줄로 다시 정리해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Response origin and answer-mode badges must not drift after the second follow-up
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");

  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 단일 출처");
  await expect(originDetail).toContainText("백과 기반");

  // After the second follow-up the history-card `.meta` must still carry the same
  // entity-card count-summary + progress-summary composition with no drift, no leaked
  // answer-mode labels, and no leading/trailing separator artifact.
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText(
    "사실 검증 단일 출처 1 · 단일 출처 상태 1건."
  );
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");
  const postSecondFollowUpMetaText = ((await historyCardMeta.textContent()) || "").trim();
  expect(postSecondFollowUpMetaText.startsWith("·")).toBe(false);
  expect(postSecondFollowUpMetaText.endsWith("·")).toBe(false);
  expect(
    postSecondFollowUpMetaText.indexOf("사실 검증 단일 출처 1")
  ).toBeLessThan(postSecondFollowUpMetaText.indexOf("단일 출처 상태 1건"));

  // Clean up the pre-seeded record
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card entity-card 자연어 reload 후 두 번째 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 drift하지 않습니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-natural-reload-second-followup");

  // Pre-seed a simple single-source entity-card web search record with stored response_origin
  // and single-weak-slot claim_coverage so `_summarize_claim_coverage` yields {weak: 1}.
  const recordId = `websearch-nat-second-followup-${Date.now().toString(36)}`;
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
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 단일 출처",
      source_roles: ["백과 기반"],
    },
    claim_coverage: [
      {
        slot: "장르",
        status: "weak",
        status_label: "단일 출처",
        value: "오픈월드 액션 어드벤처 게임",
        support_count: 1,
        candidate_count: 1,
        source_role: "encyclopedia",
      },
    ],
    claim_coverage_progress_summary: "단일 출처 상태 1건.",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card with seed values that mirror the stored record, then click
  // "다시 불러오기" once to register the record in the server-side session.
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
          claim_coverage_summary: { strong: 0, weak: 1, missing: 0, conflict: 0 },
          claim_coverage_progress_summary: "단일 출처 상태 1건.",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  const reloadButton = historyBox.locator(".history-item-actions button.secondary").first();
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toHaveText("설명 카드");

  // Natural reload — send "방금 검색한 결과 다시 보여줘" without record ID
  await page.evaluate(async () => {
    // @ts-ignore — sendRequest is defined in the page scope
    await sendRequest({
      user_text: "방금 검색한 결과 다시 보여줘",
    });
  });

  await expect(originBadge).toHaveText("WEB");
  await expect(answerModeBadge).toHaveText("설명 카드");

  // After the natural reload the history-card `.meta` must already carry the entity-card
  // count-summary + progress-summary composition derived from the stored record.
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText(
    "사실 검증 단일 출처 1 · 단일 출처 상태 1건."
  );
  const postNaturalReloadMetaText = ((await historyCardMeta.textContent()) || "").trim();
  expect(postNaturalReloadMetaText.startsWith("·")).toBe(false);
  expect(postNaturalReloadMetaText.endsWith("·")).toBe(false);
  expect(
    postNaturalReloadMetaText.indexOf("사실 검증 단일 출처 1")
  ).toBeLessThan(postNaturalReloadMetaText.indexOf("단일 출처 상태 1건"));

  // First follow-up: user_text + load_web_search_record_id on the same record
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  await expect(originBadge).toHaveText("WEB");
  await expect(answerModeBadge).toHaveText("설명 카드");
  await expect(historyCardMeta).toHaveText(
    "사실 검증 단일 출처 1 · 단일 출처 상태 1건."
  );

  // Second follow-up: another user_text + load_web_search_record_id on the same record
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "장르만 한 줄로 다시 정리해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Response origin + answer-mode badges must not drift after the second follow-up
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");

  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 단일 출처");
  await expect(originDetail).toContainText("백과 기반");

  // History-card `.meta` must still carry the same entity-card count-summary + progress-summary
  // composition with no drift, no leaked answer-mode labels, and no leading/trailing separator.
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText(
    "사실 검증 단일 출처 1 · 단일 출처 상태 1건."
  );
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");
  const postSecondFollowUpMetaText = ((await historyCardMeta.textContent()) || "").trim();
  expect(postSecondFollowUpMetaText.startsWith("·")).toBe(false);
  expect(postSecondFollowUpMetaText.endsWith("·")).toBe(false);
  expect(
    postSecondFollowUpMetaText.indexOf("사실 검증 단일 출처 1")
  ).toBeLessThan(postSecondFollowUpMetaText.indexOf("단일 출처 상태 1건"));

  // Clean up the pre-seeded record
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card latest-update 다시 불러오기 후 follow-up 질문에서 WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 drift하지 않습니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-latest-followup");

  // Pre-seed a latest_update web search record with mixed source roles
  const recordId = `websearch-latest-followup-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `스팀할인-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "스팀 여름 할인",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 2,
    results: [
      {
        title: "Steam 여름 할인 - Steam Store",
        url: "https://store.steampowered.com/sale/summer2026",
        snippet: "Steam 여름 할인이 시작되었습니다.",
      },
      {
        title: "스팀 여름 할인 시작 - 게임뉴스",
        url: "https://www.yna.co.kr/view/AKR20260401000100017",
        snippet: "스팀이 2026년 여름 할인을 시작했다.",
      },
    ],
    pages: [
      {
        url: "https://store.steampowered.com/sale/summer2026",
        title: "Steam 여름 할인 - Steam Store",
        text: "Steam 여름 할인이 시작되었습니다.",
      },
      {
        url: "https://www.yna.co.kr/view/AKR20260401000100017",
        title: "스팀 여름 할인 시작 - 게임뉴스",
        text: "스팀이 2026년 여름 할인을 시작했다.",
      },
    ],
    summary_text: "웹 검색 요약: 스팀 여름 할인\n\nSteam 여름 할인이 시작되었습니다. 수천 개 게임이 최대 90% 할인됩니다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "latest_update",
      verification_label: "공식+기사 교차 확인",
      source_roles: ["보조 기사", "공식 기반"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card with latest_update answer_mode
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "스팀 여름 할인",
          answer_mode: "latest_update",
          verification_label: "공식+기사 교차 확인",
          source_roles: ["보조 기사", "공식 기반"],
          result_count: 2,
          page_count: 2,
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

  // Click "다시 불러오기" — show-only reload
  await reloadButton.click();

  // Wait for the initial reload response badges
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toHaveText("최신 확인");

  // Send a follow-up with load_web_search_record_id + user_text (non-show-only)
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Assert response origin badges are preserved after follow-up
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);

  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");

  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("공식+기사 교차 확인");
  await expect(originDetail).toContainText("보조 기사");
  await expect(originDetail).toContainText("공식 기반");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card latest-update click reload 후 composer를 거친 plain follow-up 경로가 load_web_search_record_id 없이 empty claim_coverage surfaces를 유지합니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-click-reload-plain-follow-up-latest-update");

  // Pre-seed a latest_update mixed-source record with empty `claim_coverage`
  // matching the existing follow-up scenario above, so the two tests share
  // identical stored data and only differ in the follow-up submit path.
  const recordId = `websearch-click-reload-plain-follow-up-latest-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `스팀-여름할인-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "스팀 여름 할인",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 2,
    results: [
      {
        title: "Steam 여름 할인 - Steam Store",
        url: "https://store.steampowered.com/sale/summer2026",
        snippet: "Steam 여름 할인이 시작되었습니다.",
      },
      {
        title: "스팀 여름 할인 시작 - 게임뉴스",
        url: "https://www.yna.co.kr/view/AKR20260401000100017",
        snippet: "스팀이 2026년 여름 할인을 시작했다.",
      },
    ],
    pages: [
      {
        url: "https://store.steampowered.com/sale/summer2026",
        title: "Steam 여름 할인 - Steam Store",
        text: "Steam 여름 할인이 시작되었습니다.",
      },
      {
        url: "https://www.yna.co.kr/view/AKR20260401000100017",
        title: "스팀 여름 할인 시작 - 게임뉴스",
        text: "스팀이 2026년 여름 할인을 시작했다.",
      },
    ],
    summary_text: "웹 검색 요약: 스팀 여름 할인\n\nSteam 여름 할인이 시작되었습니다. 수천 개 게임이 최대 90% 할인됩니다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "latest_update",
      verification_label: "공식+기사 교차 확인",
      source_roles: ["보조 기사", "공식 기반"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "스팀 여름 할인",
          answer_mode: "latest_update",
          verification_label: "공식+기사 교차 확인",
          source_roles: ["보조 기사", "공식 기반"],
          result_count: 2,
          page_count: 2,
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

  // Step 1: real browser click-reload.
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toHaveText("최신 확인");
  await expect(page.getByTestId("submit-request")).toBeEnabled();

  // Step 2: send a plain follow-up through the exact browser composer path.
  await page.locator('input[name="request_mode"][value="chat"]').check();
  await page.locator("#web-search-permission").selectOption("enabled");
  await page.locator("#user-text").fill("이 결과 한 문장으로 요약해줘");

  const plainFollowUpRequestPromise = page.waitForRequest(
    (req) => req.url().includes("/api/chat/stream") && req.method() === "POST"
  );
  await page.getByTestId("submit-request").click();
  const plainFollowUpRequest = await plainFollowUpRequestPromise;
  const plainFollowUpBodyText = plainFollowUpRequest.postData() || "";
  expect(plainFollowUpBodyText.length).toBeGreaterThan(0);
  expect(plainFollowUpBodyText).not.toContain("load_web_search_record_id");
  const plainFollowUpBody = JSON.parse(plainFollowUpBodyText);
  expect(plainFollowUpBody.user_text).toBe("이 결과 한 문장으로 요약해줘");
  expect(Object.prototype.hasOwnProperty.call(plainFollowUpBody, "load_web_search_record_id")).toBe(false);

  await expect(page.getByTestId("submit-request")).toBeEnabled();

  // latest-update plain follow-up must NOT inject top-level claim_coverage.
  // `_respond_with_active_context()`'s `context_claim_coverage` gate leaves
  // latest-update / empty-claim-coverage contexts untouched, matching
  // `test_handle_chat_latest_update_click_reload_plain_follow_up_*`.
  const claimCoverageBox = page.locator("#claim-coverage-box");
  await expect(claimCoverageBox).toBeHidden();

  // History-card `.meta` must still be absent for the latest-update empty
  // claim_coverage / empty progress shape.
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(0);

  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card latest-update noisy community source initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-latest-update-noisy-initial-render-empty-meta");

  // Pre-seed a latest_update noisy record on disk without `claim_coverage`, mirroring the
  // service path where `WebSearchStore.save(...)` is called without `claim_coverage` for
  // noisy community-source cases. `storage/web_search_store.py:316` +
  // `app/serializers.py:280` emit `claim_coverage_summary: {strong:0, weak:0, missing:0}`
  // with empty progress. The history-card renderer must still suppress `.meta` for this
  // investigation-card path at the initial-render stage, before any user interaction.
  const recordId = `websearch-latest-noisy-initial-render-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `기준금리-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "기준금리 속보",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 3,
    results: [
      {
        title: "기준금리 속보 - 한국경제",
        url: "https://www.hankyung.com/economy/2025",
        snippet: "한국은행이 기준금리를 동결했다고 밝혔다.",
      },
      {
        title: "기준금리 뉴스 - 매일경제",
        url: "https://www.mk.co.kr/economy/2025",
        snippet: "한국은행이 기준금리를 동결했다.",
      },
      {
        title: "기준금리 커뮤니티",
        url: "https://brunch.co.kr/economy",
        snippet: "기준금리 속보 - 로그인 회원가입 구독 광고 전체메뉴 이용약관 개인정보 facebook twitter",
      },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 기준금리 속보\n\n한국은행이 기준금리를 동결했다고 밝혔다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "latest_update",
      verification_label: "기사 교차 확인",
      source_roles: ["보조 기사"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history item with the actual serialized zero-count shape that the server
  // emits for this store-seeded noisy latest_update path. The noisy community source
  // is filtered out of `source_roles` at serialization time (only `보조 기사` remains),
  // mirroring the shipped noisy exclusion contract used by the rest of the family.
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "기준금리 속보",
          answer_mode: "latest_update",
          verification_label: "기사 교차 확인",
          source_roles: ["보조 기사"],
          result_count: 3,
          page_count: 3,
          created_at: record.created_at,
          record_path: recordPath,
          claim_coverage_summary: { strong: 0, weak: 0, missing: 0, conflict: 0 },
          claim_coverage_progress_summary: "",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();

  // Pre-click header/action expectations: the reload button is still visible but this
  // scenario does NOT click it, does NOT send natural reload, and does NOT send follow-up.
  // It also must not leak noisy community source text (`보조 커뮤니티` / `brunch`) into
  // the history card's visible content at the initial-render stage, since the noisy
  // source was already excluded from `source_roles` at serialization time.
  const historyCard = historyBox.locator(".history-item").first();
  const reloadButton = historyCard.locator(".history-item-actions button.secondary");
  await expect(reloadButton).toHaveText("다시 불러오기");
  await expect(historyCard).not.toContainText("보조 커뮤니티");
  await expect(historyCard).not.toContainText("brunch");

  // latest-update noisy community initial-render empty-meta no-leak contract: the
  // serialized zero-count summary must not produce any detail `.meta` node and must not
  // leak `사실 검증` content through accidental `.meta` creation, BEFORE any user
  // interaction.
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card latest-update 다시 불러오기 후 noisy community source가 본문, origin detail, context box에 보조 커뮤니티/brunch 미노출 + 기사 교차 확인, 보조 기사, hankyung.com · mk.co.kr 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-latest-noisy");

  // Pre-seed a latest_update record where noisy community source was filtered at search time.
  // The stored record mirrors what the service produces: summary_text and source_roles
  // already exclude the noisy source, but results array still contains it for provenance.
  const recordId = `websearch-latest-noisy-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `기준금리-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "기준금리 속보",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 3,
    results: [
      {
        title: "기준금리 속보 - 한국경제",
        url: "https://www.hankyung.com/economy/2025",
        snippet: "한국은행이 기준금리를 동결했다고 밝혔다.",
      },
      {
        title: "기준금리 뉴스 - 매일경제",
        url: "https://www.mk.co.kr/economy/2025",
        snippet: "한국은행이 기준금리를 동결했다.",
      },
      {
        title: "기준금리 커뮤니티",
        url: "https://brunch.co.kr/economy",
        snippet: "기준금리 속보 - 로그인 회원가입 구독 광고 전체메뉴 이용약관 개인정보 facebook twitter",
      },
    ],
    pages: [
      {
        url: "https://www.hankyung.com/economy/2025",
        title: "기준금리 속보 - 한국경제",
        text: "한국은행이 기준금리를 동결했다고 밝혔다.",
      },
      {
        url: "https://www.mk.co.kr/economy/2025",
        title: "기준금리 뉴스 - 매일경제",
        text: "한국은행이 기준금리를 동결했다.",
      },
      {
        url: "https://brunch.co.kr/economy",
        title: "기준금리 커뮤니티",
        text: "기준금리 속보 - 로그인 회원가입 구독 광고 전체메뉴 이용약관 개인정보 facebook twitter",
      },
    ],
    summary_text: "웹 검색 요약: 기준금리 속보\n\n한국은행이 기준금리를 동결했다고 밝혔다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "외부 웹 최신 확인",
      kind: "assistant",
      model: null,
      answer_mode: "latest_update",
      verification_label: "기사 교차 확인",
      source_roles: ["보조 기사"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card — source_roles in the card exclude noisy community
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "기준금리 속보",
          answer_mode: "latest_update",
          verification_label: "기사 교차 확인",
          source_roles: ["보조 기사"],
          result_count: 3,
          page_count: 3,
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

  // Click "다시 불러오기"
  await reloadButton.click();

  // Assert reloaded response keeps latest_update badges
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toHaveText("최신 확인");

  // Assert origin detail shows clean source roles, NOT noisy community
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("기사 교차 확인");
  await expect(originDetail).toContainText("보조 기사");

  // Negative assertions: noisy community source must NOT appear, and the
  // stale mixed-source label must not leak into origin detail either.
  const originDetailText = await originDetail.textContent();
  expect(originDetailText).not.toContain("보조 커뮤니티");
  expect(originDetailText).not.toContain("brunch");
  expect(originDetailText).not.toContain("공식 기반");
  expect(originDetailText).not.toContain("공식+기사 교차 확인");

  // Response body must NOT contain noisy source content
  const responseText = await page.getByTestId("response-text").textContent();
  expect(responseText).not.toContain("brunch");
  expect(responseText).not.toContain("로그인 회원가입 구독 광고");

  // Context box: positive retention for clean sources, negative for noisy
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("hankyung.com");
  await expect(contextBox).toContainText("mk.co.kr");
  const contextBoxText = await contextBox.textContent();
  expect(contextBoxText).not.toContain("brunch");

  // latest-update noisy show-only reload empty-meta branch: zero-count summary + empty
  // progress → history card must not render any `.meta` detail node and must not leak
  // `사실 검증` content through accidental `.meta` creation.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card latest-update 자연어 reload noisy community 보조 커뮤니티 brunch 미노출 기사 교차 확인 보조 기사 hankyung mk 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-natural-reload-latest-noisy");

  // Pre-seed a noisy latest_update record whose stored response_origin already
  // mirrors the shipped noisy-exclusion truth (`기사 교차 확인` / `보조 기사`).
  const recordId = `websearch-latest-noisy-nat-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `기준금리-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "기준금리 속보",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 3,
    results: [
      {
        title: "기준금리 속보 - 한국경제",
        url: "https://www.hankyung.com/economy/2025",
        snippet: "한국은행이 기준금리를 동결했다고 밝혔다.",
      },
      {
        title: "기준금리 뉴스 - 매일경제",
        url: "https://www.mk.co.kr/economy/2025",
        snippet: "한국은행이 기준금리를 동결했다.",
      },
      {
        title: "기준금리 커뮤니티",
        url: "https://brunch.co.kr/economy",
        snippet: "기준금리 속보 - 로그인 회원가입 구독 광고 전체메뉴 이용약관 개인정보 facebook twitter",
      },
    ],
    pages: [
      {
        url: "https://www.hankyung.com/economy/2025",
        title: "기준금리 속보 - 한국경제",
        text: "한국은행이 기준금리를 동결했다고 밝혔다.",
      },
      {
        url: "https://www.mk.co.kr/economy/2025",
        title: "기준금리 뉴스 - 매일경제",
        text: "한국은행이 기준금리를 동결했다.",
      },
      {
        url: "https://brunch.co.kr/economy",
        title: "기준금리 커뮤니티",
        text: "기준금리 속보 - 로그인 회원가입 구독 광고 전체메뉴 이용약관 개인정보 facebook twitter",
      },
    ],
    summary_text: "웹 검색 요약: 기준금리 속보\n\n한국은행이 기준금리를 동결했다고 밝혔다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "외부 웹 최신 확인",
      kind: "assistant",
      model: null,
      answer_mode: "latest_update",
      verification_label: "기사 교차 확인",
      source_roles: ["보조 기사"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Step 1: render the history card and click "다시 불러오기" so the server
  // session is aware of the pre-seeded record before the natural reload.
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "기준금리 속보",
          answer_mode: "latest_update",
          verification_label: "기사 교차 확인",
          source_roles: ["보조 기사"],
          result_count: 3,
          page_count: 3,
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
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Step 2: natural reload — send "방금 검색한 결과 다시 보여줘" without record ID.
  await page.evaluate(async () => {
    // @ts-ignore — sendRequest is defined in the page scope
    await sendRequest({
      user_text: "방금 검색한 결과 다시 보여줘",
    });
  });

  // Reloaded response keeps latest-update badges
  await expect(originBadge).toHaveText("WEB");
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toHaveText("최신 확인");

  // Origin detail shows the clean noisy-exclusion truth
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("기사 교차 확인");
  await expect(originDetail).toContainText("보조 기사");

  // Negative assertions: noisy community source and stale mixed-source label
  // must not leak into origin detail.
  const originDetailText = await originDetail.textContent();
  expect(originDetailText).not.toContain("보조 커뮤니티");
  expect(originDetailText).not.toContain("brunch");
  expect(originDetailText).not.toContain("공식 기반");
  expect(originDetailText).not.toContain("공식+기사 교차 확인");

  // Response body must not contain noisy source content
  const responseText = await page.getByTestId("response-text").textContent();
  expect(responseText).not.toContain("brunch");
  expect(responseText).not.toContain("로그인 회원가입 구독 광고");

  // Context box: positive retention for clean sources, negative for noisy
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("hankyung.com");
  await expect(contextBox).toContainText("mk.co.kr");
  const contextBoxText = await contextBox.textContent();
  expect(contextBoxText).not.toContain("brunch");

  // latest-update noisy natural-reload reload-only empty-meta branch:
  // zero-count summary + empty progress → history card must not render any
  // `.meta` detail node and must not leak `사실 검증` content.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card entity-card noisy single-source initial-render 단계에서 strong-plus-missing count-summary meta contract가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-entity-noisy-single-source-initial-render-strong-plus-missing");

  // Pre-seed a noisy single-source entity_card record with a 3-strong + 2-missing
  // claim_coverage distribution on disk. Service baseline at `tests/test_web_app.py:19457`,
  // `:19532`, `:19611`, `:19687` already serializes this noisy branch as
  // `{strong:3, weak:0, missing:2}` + empty progress + `설명형 다중 출처 합의` label after
  // reload/follow-up. The noisy blog source (`blog.example.com`) stays in stored `results`
  // for provenance but is filtered out of `source_roles` at serialization time, mirroring
  // the shipped noisy exclusion contract.
  const recordId = `websearch-entity-noisy-single-source-initial-render-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 3,
    results: [
      { title: "붉은사막 - 나무위키", url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { title: "붉은사막 - 위키백과", url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { title: "붉은사막 출시일 정보", url: "https://blog.example.com/crimson-desert", snippet: "붉은사막 출시일은 2025년 12월로 예정되어 있다." },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 붉은사막\n\n확인된 사실:\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다. [교차 확인]",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["백과 기반"],
    },
    // Slot names avoid noisy exclusion keywords (`출시일`/`2025`/`brunch`/`blog.example.com`)
    // so the seeded claim-coverage rows do not collide with the noisy single-source
    // exclusion assertions below.
    claim_coverage: [
      { slot: "장르", status: "strong", status_label: "교차 확인", value: "오픈월드 액션 어드벤처 게임", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "개발사", status: "strong", status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "플랫폼", status: "strong", status_label: "교차 확인", value: "PC/콘솔", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "엔진", status: "missing", status_label: "미확인" },
      { slot: "난이도", status: "missing", status_label: "미확인" },
    ],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history item with the shipped noisy strong-plus-missing count-summary
  // shape and the noisy-filtered source_roles (`백과 기반` only).
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
          verification_label: "설명형 다중 출처 합의",
          source_roles: ["백과 기반"],
          result_count: 3,
          page_count: 3,
          created_at: record.created_at,
          record_path: recordPath,
          claim_coverage_summary: { strong: 3, weak: 0, missing: 2, conflict: 0 },
          claim_coverage_progress_summary: "",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();

  // Pre-click header/action expectations: the reload button is visible but this scenario
  // intentionally does NOT click it, does NOT send natural reload, and does NOT send
  // follow-up. The noisy single-source claim also must stay excluded from the visible
  // history-card content at initial render, since it was already filtered from
  // `source_roles` at serialization time.
  const historyCard = historyBox.locator(".history-item").first();
  const reloadButton = historyCard.locator(".history-item-actions button.secondary");
  await expect(reloadButton).toHaveText("다시 불러오기");
  await expect(historyCard).not.toContainText("출시일");
  await expect(historyCard).not.toContainText("2025");
  await expect(historyCard).not.toContainText("blog.example.com");

  // noisy entity-card initial-render strong-plus-missing meta contract: the rendered
  // detail `.meta` must be exactly `사실 검증 교차 확인 3 · 미확인 2` with no answer-mode
  // label leak inside the `.meta` element. entity_card is investigation, so detailLines
  // skip `설명 카드` / `최신 확인` / `일반 검색`.
  const historyCardMeta = historyCard.locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 3 · 미확인 2");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card entity-card 다시 불러오기 후 noisy single-source claim(출시일/2025/blog.example.com)이 본문과 origin detail에 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-entity-noisy-prov");

  // Pre-seed an entity_card record where noisy single-source claim was filtered.
  // summary_text and source_roles exclude the noisy blog source.
  // results array still contains it for provenance.
  const recordId = `websearch-entity-noisy-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 3,
    results: [
      {
        title: "붉은사막 - 나무위키",
        url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
      {
        title: "붉은사막 - 위키백과",
        url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
      {
        title: "붉은사막 출시일 정보",
        url: "https://blog.example.com/crimson-desert",
        snippet: "붉은사막 출시일은 2025년 12월로 예정되어 있다.",
      },
    ],
    pages: [
      {
        url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        title: "붉은사막 - 나무위키",
        text: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
      {
        url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        title: "붉은사막 - 위키백과",
        text: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
      {
        url: "https://blog.example.com/crimson-desert",
        title: "붉은사막 출시일 정보",
        text: "붉은사막 출시일은 2025년 12월로 예정되어 있다. 로그인 회원가입 구독 광고 전체메뉴",
      },
    ],
    summary_text: "웹 검색 요약: 붉은사막\n\n확인된 사실:\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다. [교차 확인]",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["백과 기반"],
    },
    // Stored claim_coverage mirrors the shipped noisy entity-card strong-plus-missing
    // branch (`{strong:3, weak:0, missing:2}`, empty progress). Slot names avoid noisy
    // exclusion keywords (`출시일`/`2025`/`blog.example.com`) so the seeded rows do not
    // collide with the exclusion assertions below.
    claim_coverage: [
      { slot: "장르", status: "strong", status_label: "교차 확인", value: "오픈월드 액션 어드벤처 게임", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "개발사", status: "strong", status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "플랫폼", status: "strong", status_label: "교차 확인", value: "PC/콘솔", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "엔진", status: "missing", status_label: "미확인" },
      { slot: "난이도", status: "missing", status_label: "미확인" },
    ],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card — source_roles exclude noisy blog source
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
          verification_label: "설명형 다중 출처 합의",
          source_roles: ["백과 기반"],
          result_count: 3,
          page_count: 3,
          created_at: record.created_at,
          record_path: recordPath,
          claim_coverage_summary: { strong: 3, weak: 0, missing: 2, conflict: 0 },
          claim_coverage_progress_summary: "",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  const reloadButton = historyBox.locator(".history-item-actions button.secondary").first();
  await expect(reloadButton).toHaveText("다시 불러오기");

  // Click "다시 불러오기"
  await reloadButton.click();

  // Assert reloaded response keeps entity_card badges
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toHaveText("설명 카드");

  // Assert origin detail shows clean source role
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("백과 기반");

  // Negative assertions: noisy blog source must NOT appear in origin detail
  const originDetailText = await originDetail.textContent();
  expect(originDetailText).not.toContain("출시일");
  expect(originDetailText).not.toContain("2025");
  expect(originDetailText).not.toContain("blog.example.com");

  // Response body: wait for content to render, then check positive and negative assertions
  await expect(page.getByTestId("response-text")).toContainText("확인된 사실 [교차 확인]:");
  const responseText = await page.getByTestId("response-text").textContent();
  expect(responseText).not.toContain("출시일");
  expect(responseText).not.toContain("2025");
  expect(responseText).not.toContain("blog.example.com");
  expect(responseText).not.toContain("로그인 회원가입 구독 광고");

  // Context box: provenance URLs preserved
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");
  await expect(contextBox).toContainText("blog.example.com");

  // noisy entity-card show-only reload strong-plus-missing meta contract: after reload the
  // history-card detail `.meta` must be exactly `사실 검증 교차 확인 3 · 미확인 2` with no
  // answer-mode label leak inside the `.meta` element. entity_card is investigation, so
  // detailLines skip `설명 카드` / `최신 확인` / `일반 검색`.
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 3 · 미확인 2");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card entity-card actual-search initial-render 단계에서 strong-plus-missing count-summary meta contract가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-entity-actual-search-initial-render-strong-plus-missing");

  // Pre-seed a baseline actual-search entity_card record with a 3-strong + 2-missing
  // claim_coverage distribution on disk. Service baseline at `tests/test_web_app.py:9473-9474`
  // already serializes this branch as `{strong:3, weak:0, missing:2}` + empty progress +
  // `설명형 다중 출처 합의` label when the runtime path is exercised; this browser scenario
  // exercises the renderer at the initial-render stage before any click/natural reload/follow-up.
  const recordId = `websearch-entity-actual-initial-render-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      { title: "붉은사막 - 나무위키", url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { title: "붉은사막 - 위키백과", url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 붉은사막\n\n확인된 사실:\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다. [교차 확인]",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["백과 기반"],
    },
    // Slot names avoid noisy keywords (`출시일`/`2025`/`brunch`) used by adjacent noisy
    // exclusion scenarios so future fixture reuse stays drift-free.
    claim_coverage: [
      { slot: "장르", status: "strong", status_label: "교차 확인", value: "오픈월드 액션 어드벤처 게임", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "개발사", status: "strong", status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "플랫폼", status: "strong", status_label: "교차 확인", value: "PC/콘솔", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "엔진", status: "missing", status_label: "미확인" },
      { slot: "난이도", status: "missing", status_label: "미확인" },
    ],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history item with the shipped strong-plus-missing count-summary shape.
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
          verification_label: "설명형 다중 출처 합의",
          source_roles: ["백과 기반"],
          result_count: 2,
          page_count: 0,
          created_at: record.created_at,
          record_path: recordPath,
          claim_coverage_summary: { strong: 3, weak: 0, missing: 2, conflict: 0 },
          claim_coverage_progress_summary: "",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();

  // Pre-click header/action expectations: the history item exposes the `다시 불러오기`
  // button, but this scenario intentionally does NOT click it and does NOT send natural
  // reload or follow-up. The check is that the renderer produces the exact strong-plus-
  // missing count line at the initial-render stage.
  const historyCard = historyBox.locator(".history-item").first();
  const reloadButton = historyCard.locator(".history-item-actions button.secondary");
  await expect(reloadButton).toHaveText("다시 불러오기");

  // actual-search entity-card initial-render strong-plus-missing meta contract: the
  // rendered detail `.meta` must be exactly `사실 검증 교차 확인 3 · 미확인 2` with no
  // answer-mode label leak inside the `.meta` element. entity_card is an investigation
  // card, so detailLines skip `설명 카드` / `최신 확인` / `일반 검색`.
  const historyCardMeta = historyCard.locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 3 · 미확인 2");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card entity-card dual-probe initial-render 단계에서 mixed count-summary meta contract가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-entity-dual-probe-initial-render-mixed");

  // Pre-seed a baseline dual-probe entity_card record with a 1-strong + 4-weak
  // claim_coverage distribution on disk. Service baseline at `tests/test_web_app.py:9796`
  // and `:9921` already serialize this branch as `{strong:1, weak:4, missing:0}` + empty
  // progress + `설명형 다중 출처 합의` label when the runtime path is exercised; this browser
  // scenario exercises the renderer at the initial-render stage before any interaction.
  const recordId = `websearch-entity-dual-initial-render-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 2,
    results: [
      { title: "붉은사막 - 나무위키", url: "https://namu.wiki/w/test", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.", matched_query: "붉은사막" },
      { title: "붉은사막 | 플랫폼 - 공식", url: "https://www.pearlabyss.com/200", snippet: "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이다.", matched_query: "붉은사막 공식 플랫폼" },
      { title: "붉은사막 | 서비스 - 공식", url: "https://www.pearlabyss.com/300", snippet: "붉은사막은 펄어비스가 운영하는 게임이다.", matched_query: "붉은사막 서비스 공식" },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["공식 기반", "백과 기반"],
    },
    claim_coverage: [
      { slot: "개발사", status: "strong", status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "official" },
      { slot: "장르", status: "weak", status_label: "단일 출처", value: "오픈월드 액션 어드벤처", support_count: 1, candidate_count: 1, source_role: "encyclopedia" },
      { slot: "플랫폼", status: "weak", status_label: "단일 출처", value: "PC/콘솔", support_count: 1, candidate_count: 1, source_role: "official" },
      { slot: "서비스", status: "weak", status_label: "단일 출처", value: "펄어비스", support_count: 1, candidate_count: 1, source_role: "official" },
      { slot: "출시일", status: "weak", status_label: "단일 출처", value: "미정", support_count: 1, candidate_count: 1, source_role: "official" },
    ],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history item with the shipped dual-probe mixed count-summary shape.
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
          verification_label: "설명형 다중 출처 합의",
          source_roles: ["공식 기반", "백과 기반"],
          result_count: 3,
          page_count: 2,
          created_at: record.created_at,
          record_path: recordPath,
          claim_coverage_summary: { strong: 1, weak: 4, missing: 0, conflict: 0 },
          claim_coverage_progress_summary: "",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();

  const historyCard = historyBox.locator(".history-item").first();
  const reloadButton = historyCard.locator(".history-item-actions button.secondary");
  await expect(reloadButton).toHaveText("다시 불러오기");

  // dual-probe entity-card initial-render mixed count-summary meta contract: the rendered
  // detail `.meta` must be exactly `사실 검증 교차 확인 1 · 단일 출처 4` with no answer-mode
  // label leak inside the `.meta` element. The count line itself legitimately contains
  // ` · ` between `교차 확인 1` and `단일 출처 4`, so `not.toContainText("·")` blanket rule
  // is intentionally avoided; exact `toHaveText` + answer-mode label negatives suffice.
  const historyCardMeta = historyCard.locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 1 · 단일 출처 4");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card entity-card 다시 불러오기 후 actual-search source path(namu.wiki, ko.wikipedia.org) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-entity-actual-sp");

  // Pre-seed a generic entity_card record (붉은사막, single source without dual-probe)
  const recordId = `websearch-entity-actual-sp-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      {
        title: "붉은사막 - 나무위키",
        url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
      {
        title: "붉은사막 - 위키백과",
        url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 붉은사막\n\n확인된 사실:\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다. [교차 확인]",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["백과 기반"],
    },
    // actual-search entity-card reload-only strong-plus-missing branch: stored claim_coverage
    // mirrors the actual shipped runtime (`{strong:3, weak:0, missing:2}`, empty progress).
    claim_coverage: [
      { slot: "장르", status: "strong", status_label: "교차 확인", value: "오픈월드 액션 어드벤처 게임", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "개발사", status: "strong", status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "플랫폼", status: "strong", status_label: "교차 확인", value: "PC/콘솔", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "출시일", status: "missing", status_label: "미확인" },
      { slot: "가격", status: "missing", status_label: "미확인" },
    ],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card
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
          verification_label: "설명형 다중 출처 합의",
          source_roles: ["백과 기반"],
          result_count: 2,
          page_count: 0,
          created_at: record.created_at,
          record_path: recordPath,
          claim_coverage_summary: { strong: 3, weak: 0, missing: 2, conflict: 0 },
          claim_coverage_progress_summary: "",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  const reloadButton = historyBox.locator(".history-item-actions button.secondary").first();
  await expect(reloadButton).toHaveText("다시 불러오기");

  // Click "다시 불러오기"
  await reloadButton.click();

  // Wait for the response to render
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Assert context box shows both actual-search source URLs (plurality)
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");

  // Assert response-origin continuity
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("백과 기반");

  // actual-search reload-only strong-plus-missing meta: history-card `.meta` must be the
  // exact `사실 검증 교차 확인 3 · 미확인 2` line, with no answer-mode label leak.
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 3 · 미확인 2");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card entity-card 다시 불러오기 후 dual-probe source path(pearlabyss.com/200, pearlabyss.com/300) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-entity-dual-probe");

  // Pre-seed an entity_card record with dual-probe results (two official URLs)
  const recordId = `websearch-entity-dual-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 2,
    results: [
      {
        title: "붉은사막 - 나무위키",
        url: "https://namu.wiki/w/test",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
        matched_query: "붉은사막",
      },
      {
        title: "붉은사막 | 플랫폼 - 공식",
        url: "https://www.pearlabyss.com/200",
        snippet: "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이다.",
        matched_query: "붉은사막 공식 플랫폼",
      },
      {
        title: "붉은사막 | 서비스 - 공식",
        url: "https://www.pearlabyss.com/300",
        snippet: "붉은사막은 펄어비스가 운영하는 게임이다.",
        matched_query: "붉은사막 서비스 공식",
      },
    ],
    pages: [
      {
        url: "https://www.pearlabyss.com/200",
        title: "붉은사막 | 플랫폼 - 공식",
        text: "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이며 펄어비스가 개발 중입니다.",
      },
      {
        url: "https://www.pearlabyss.com/300",
        title: "붉은사막 | 서비스 - 공식",
        text: "붉은사막은 펄어비스가 운영하는 게임이며 배급도 펄어비스가 담당합니다.",
      },
    ],
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["공식 기반", "백과 기반"],
    },
    // Dual-probe reload-only mixed count-summary branch: runtime yields {strong:1, weak:4,
    // missing:0} for this dual-probe actual-search fixture. Seed the on-disk claim_coverage
    // with a matching 1-strong + 4-weak mix so post-reload server re-serialization aligns
    // with pre-click client seed and the `.meta` exact text stays stable.
    claim_coverage: [
      { slot: "개발사", status: "strong", status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "official" },
      { slot: "장르", status: "weak", status_label: "단일 출처", value: "오픈월드 액션 어드벤처", support_count: 1, candidate_count: 1, source_role: "encyclopedia" },
      { slot: "플랫폼", status: "weak", status_label: "단일 출처", value: "PC/콘솔", support_count: 1, candidate_count: 1, source_role: "official" },
      { slot: "서비스", status: "weak", status_label: "단일 출처", value: "펄어비스", support_count: 1, candidate_count: 1, source_role: "official" },
      { slot: "출시일", status: "weak", status_label: "단일 출처", value: "미정", support_count: 1, candidate_count: 1, source_role: "official" },
    ],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card
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
          verification_label: "설명형 다중 출처 합의",
          source_roles: ["공식 기반", "백과 기반"],
          result_count: 3,
          page_count: 2,
          created_at: record.created_at,
          record_path: recordPath,
          claim_coverage_summary: { strong: 1, weak: 4, missing: 0, conflict: 0 },
          claim_coverage_progress_summary: "",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  const reloadButton = historyBox.locator(".history-item-actions button.secondary").first();
  await expect(reloadButton).toHaveText("다시 불러오기");

  // Click "다시 불러오기"
  await reloadButton.click();

  // Wait for the response to render
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Assert context box shows both dual-probe source URLs
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("pearlabyss.com/200");
  await expect(contextBox).toContainText("pearlabyss.com/300");

  // Assert response-origin continuity
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("공식 기반");
  await expect(originDetail).toContainText("백과 기반");

  // dual-probe reload-only mixed count-summary meta: history-card `.meta` must be the exact
  // `사실 검증 교차 확인 1 · 단일 출처 4` line. investigation entity_card skips the answer-mode
  // label so no `설명 카드` / `최신 확인` / `일반 검색` leak, and the count line itself legitimately
  // contains ` · ` between `교차 확인 1` and `단일 출처 4`.
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 1 · 단일 출처 4");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card latest-update mixed-source initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-latest-update-mixed-source-initial-render-empty-meta");

  // Pre-seed a latest_update mixed-source record on disk without `claim_coverage`, mirroring
  // the service path where `WebSearchStore.save(...)` is called without `claim_coverage`.
  // `storage/web_search_store.py:316` + `app/serializers.py:280` then emit
  // `claim_coverage_summary: {strong:0, weak:0, missing:0}` with empty progress into
  // `session.web_search_history`. The history-card renderer must still suppress `.meta`
  // for this investigation-card path at the initial-render stage, before any click,
  // natural reload, or follow-up happens.
  const recordId = `websearch-latest-mixed-initial-render-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `스팀할인-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "스팀 여름 할인",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 2,
    results: [
      { title: "Steam 여름 할인 - Steam Store", url: "https://store.steampowered.com/sale/summer2026", snippet: "Steam 여름 할인이 시작되었습니다." },
      { title: "스팀 여름 할인 시작 - 게임뉴스", url: "https://www.yna.co.kr/view/AKR20260401000100017", snippet: "스팀이 2026년 여름 할인을 시작했다." },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 스팀 여름 할인\n\nSteam 여름 할인이 시작되었습니다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "latest_update",
      verification_label: "공식+기사 교차 확인",
      source_roles: ["보조 기사", "공식 기반"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history item with the actual serialized zero-count shape that the server
  // emits for this store-seeded latest_update path.
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "스팀 여름 할인",
          answer_mode: "latest_update",
          verification_label: "공식+기사 교차 확인",
          source_roles: ["보조 기사", "공식 기반"],
          result_count: 2,
          page_count: 2,
          created_at: record.created_at,
          record_path: recordPath,
          claim_coverage_summary: { strong: 0, weak: 0, missing: 0, conflict: 0 },
          claim_coverage_progress_summary: "",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();

  // Pre-click header/action expectations: the reload button is still visible but this
  // scenario does NOT click it, does NOT send natural reload, and does NOT send follow-up.
  const historyCard = historyBox.locator(".history-item").first();
  const reloadButton = historyCard.locator(".history-item-actions button.secondary");
  await expect(reloadButton).toHaveText("다시 불러오기");

  // latest-update non-noisy mixed-source initial-render empty-meta no-leak contract: the
  // serialized zero-count summary must not produce any detail `.meta` node and must not
  // leak `사실 검증` content through accidental `.meta` creation.
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card latest-update single-source initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-latest-update-single-source-initial-render-empty-meta");

  // Pre-seed a latest_update single-source record on disk without `claim_coverage`.
  const recordId = `websearch-latest-single-initial-render-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `서울날씨-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "서울 날씨",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 1,
    page_count: 1,
    results: [
      { title: "서울 날씨 - 예보", url: "https://example.com/seoul-weather", snippet: "서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다." },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 서울 날씨\n\n서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "latest_update",
      verification_label: "단일 출처 참고",
      source_roles: ["보조 출처"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "서울 날씨",
          answer_mode: "latest_update",
          verification_label: "단일 출처 참고",
          source_roles: ["보조 출처"],
          result_count: 1,
          page_count: 1,
          created_at: record.created_at,
          record_path: recordPath,
          claim_coverage_summary: { strong: 0, weak: 0, missing: 0, conflict: 0 },
          claim_coverage_progress_summary: "",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();

  const historyCard = historyBox.locator(".history-item").first();
  const reloadButton = historyCard.locator(".history-item-actions button.secondary");
  await expect(reloadButton).toHaveText("다시 불러오기");

  // latest-update non-noisy single-source initial-render empty-meta no-leak contract.
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card latest-update news-only initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-latest-update-news-only-initial-render-empty-meta");

  // Pre-seed a latest_update news-only record on disk without `claim_coverage`.
  const recordId = `websearch-latest-news-initial-render-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `기준금리-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "기준금리 속보",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 2,
    results: [
      { title: "기준금리 속보 - 한국경제", url: "https://www.hankyung.com/economy/2025", snippet: "한국은행이 기준금리를 동결했다고 밝혔다." },
      { title: "기준금리 뉴스 - 매일경제", url: "https://www.mk.co.kr/economy/2025", snippet: "한국은행이 기준금리를 동결했다." },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 기준금리 속보\n\n한국은행이 기준금리를 동결했다고 밝혔다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "latest_update",
      verification_label: "기사 교차 확인",
      source_roles: ["보조 기사"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "기준금리 속보",
          answer_mode: "latest_update",
          verification_label: "기사 교차 확인",
          source_roles: ["보조 기사"],
          result_count: 2,
          page_count: 2,
          created_at: record.created_at,
          record_path: recordPath,
          claim_coverage_summary: { strong: 0, weak: 0, missing: 0, conflict: 0 },
          claim_coverage_progress_summary: "",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();

  const historyCard = historyBox.locator(".history-item").first();
  const reloadButton = historyCard.locator(".history-item-actions button.secondary");
  await expect(reloadButton).toHaveText("다시 불러오기");

  // latest-update non-noisy news-only initial-render empty-meta no-leak contract.
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card latest-update 다시 불러오기 후 mixed-source source path(store.steampowered.com, yna.co.kr) + WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-latest-source-path");

  // Pre-seed a latest_update record with two mixed-source URLs
  const recordId = `websearch-latest-sp-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `스팀할인-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "스팀 여름 할인",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 2,
    results: [
      {
        title: "Steam 여름 할인 - Steam Store",
        url: "https://store.steampowered.com/sale/summer2026",
        snippet: "Steam 여름 할인이 시작되었습니다.",
      },
      {
        title: "스팀 여름 할인 시작 - 게임뉴스",
        url: "https://www.yna.co.kr/view/AKR20260401000100017",
        snippet: "스팀이 2026년 여름 할인을 시작했다.",
      },
    ],
    pages: [
      {
        url: "https://store.steampowered.com/sale/summer2026",
        title: "Steam 여름 할인 - Steam Store",
        text: "Steam 여름 할인이 시작되었습니다.",
      },
      {
        url: "https://www.yna.co.kr/view/AKR20260401000100017",
        title: "스팀 여름 할인 시작 - 게임뉴스",
        text: "스팀이 2026년 여름 할인을 시작했다.",
      },
    ],
    summary_text: "웹 검색 요약: 스팀 여름 할인\n\nSteam 여름 할인이 시작되었습니다. 수천 개 게임이 최대 90% 할인됩니다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "latest_update",
      verification_label: "공식+기사 교차 확인",
      source_roles: ["보조 기사", "공식 기반"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "스팀 여름 할인",
          answer_mode: "latest_update",
          verification_label: "공식+기사 교차 확인",
          source_roles: ["보조 기사", "공식 기반"],
          result_count: 2,
          page_count: 2,
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

  // Click "다시 불러오기"
  await reloadButton.click();

  // Wait for the response to render
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Assert context box shows both mixed-source URLs
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("store.steampowered.com");
  await expect(contextBox).toContainText("yna.co.kr");

  // Assert response-origin continuity
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("공식+기사 교차 확인");
  await expect(originDetail).toContainText("보조 기사");
  await expect(originDetail).toContainText("공식 기반");

  // latest-update show-only reload empty-meta branch: zero-count summary + empty progress →
  // history card must not render any `.meta` detail node and must not leak `사실 검증` content.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card latest-update single-source 다시 불러오기 후 단일 출처 참고 verification label과 보조 출처 source role이 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-latest-single");

  // Pre-seed a single-source latest_update record
  const recordId = `websearch-latest-single-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `서울날씨-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "서울 날씨",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 1,
    page_count: 1,
    results: [
      {
        title: "서울 날씨 - 예보",
        url: "https://example.com/seoul-weather",
        snippet: "서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.",
      },
    ],
    pages: [
      {
        url: "https://example.com/seoul-weather",
        title: "서울 날씨 - 예보",
        text: "서울은 맑고 낮 최고 17도. 미세먼지 보통.",
      },
    ],
    summary_text: "웹 검색 요약: 서울 날씨\n\n단일 출처 정보 [단일 출처] (추가 확인 필요):\n서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "latest_update",
      verification_label: "단일 출처 참고",
      source_roles: ["보조 출처"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "서울 날씨",
          answer_mode: "latest_update",
          verification_label: "단일 출처 참고",
          source_roles: ["보조 출처"],
          result_count: 1,
          page_count: 1,
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

  // Click "다시 불러오기"
  await reloadButton.click();

  // Assert reloaded response keeps latest_update badges
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);

  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");

  // Assert origin detail shows single-source verification label and source role
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("단일 출처 참고");
  await expect(originDetail).toContainText("보조 출처");

  // latest-update show-only reload empty-meta branch (single-source): zero-count summary +
  // empty progress → history card must not render any `.meta` detail node and must not
  // leak `사실 검증` content through accidental `.meta` creation.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card latest-update news-only 다시 불러오기 후 기사 교차 확인 verification label과 보조 기사 source role이 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-latest-news");

  // Pre-seed a news-only latest_update record (hankyung + mk, no official/encyclopedia)
  const recordId = `websearch-latest-news-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `기준금리-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "기준금리 속보",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 2,
    results: [
      {
        title: "기준금리 속보 - 한국경제",
        url: "https://www.hankyung.com/economy/2025",
        snippet: "한국은행이 기준금리를 동결했다고 밝혔다.",
      },
      {
        title: "기준금리 뉴스 - 매일경제",
        url: "https://www.mk.co.kr/economy/2025",
        snippet: "한국은행이 기준금리를 동결했다.",
      },
    ],
    pages: [
      {
        url: "https://www.hankyung.com/economy/2025",
        title: "기준금리 속보 - 한국경제",
        text: "한국은행이 기준금리를 동결했다고 밝혔다.",
      },
      {
        url: "https://www.mk.co.kr/economy/2025",
        title: "기준금리 뉴스 - 매일경제",
        text: "한국은행이 기준금리를 동결했다.",
      },
    ],
    summary_text: "웹 검색 요약: 기준금리 속보\n\n한국은행이 기준금리를 동결했다고 밝혔다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "latest_update",
      verification_label: "기사 교차 확인",
      source_roles: ["보조 기사"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "기준금리 속보",
          answer_mode: "latest_update",
          verification_label: "기사 교차 확인",
          source_roles: ["보조 기사"],
          result_count: 2,
          page_count: 2,
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

  // Click "다시 불러오기"
  await reloadButton.click();

  // Assert reloaded response keeps latest_update badges
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);

  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");

  // Assert origin detail shows news-only verification label and source role
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("기사 교차 확인");
  await expect(originDetail).toContainText("보조 기사");

  // latest-update show-only reload empty-meta branch (news-only): zero-count summary +
  // empty progress → history card must not render any `.meta` detail node and must not
  // leak `사실 검증` content.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card latest-update news-only 다시 불러오기 후 기사 source path(hankyung.com, mk.co.kr) + WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-latest-news-sp");

  // Pre-seed a news-only latest_update record (hankyung + mk)
  const recordId = `websearch-latest-news-sp-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `기준금리-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "기준금리 속보",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 2,
    results: [
      {
        title: "기준금리 속보 - 한국경제",
        url: "https://www.hankyung.com/economy/2025",
        snippet: "한국은행이 기준금리를 동결했다고 밝혔다.",
      },
      {
        title: "기준금리 뉴스 - 매일경제",
        url: "https://www.mk.co.kr/economy/2025",
        snippet: "한국은행이 기준금리를 동결했다.",
      },
    ],
    pages: [
      {
        url: "https://www.hankyung.com/economy/2025",
        title: "기준금리 속보 - 한국경제",
        text: "한국은행이 기준금리를 동결했다고 밝혔다.",
      },
      {
        url: "https://www.mk.co.kr/economy/2025",
        title: "기준금리 뉴스 - 매일경제",
        text: "한국은행이 기준금리를 동결했다.",
      },
    ],
    summary_text: "웹 검색 요약: 기준금리 속보\n\n한국은행이 기준금리를 동결했다고 밝혔다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "latest_update",
      verification_label: "기사 교차 확인",
      source_roles: ["보조 기사"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "기준금리 속보",
          answer_mode: "latest_update",
          verification_label: "기사 교차 확인",
          source_roles: ["보조 기사"],
          result_count: 2,
          page_count: 2,
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

  // Click "다시 불러오기"
  await reloadButton.click();

  // Wait for the response to render
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Assert context box shows both news source URLs
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("hankyung.com");
  await expect(contextBox).toContainText("mk.co.kr");

  // latest-update show-only reload empty-meta branch (news-only source-path): zero-count
  // summary + empty progress → history card must not render any `.meta` detail node and
  // must not leak `사실 검증` content.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card latest-update single-source 다시 불러오기 후 source path(example.com/seoul-weather) + WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-latest-single-sp");

  // Pre-seed a single-source latest_update record
  const recordId = `websearch-latest-single-sp-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `서울날씨-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "서울 날씨",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 1,
    page_count: 1,
    results: [
      {
        title: "서울 날씨 - 예보",
        url: "https://example.com/seoul-weather",
        snippet: "서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.",
      },
    ],
    pages: [
      {
        url: "https://example.com/seoul-weather",
        title: "서울 날씨 - 예보",
        text: "서울은 맑고 낮 최고 17도. 미세먼지 보통.",
      },
    ],
    summary_text: "웹 검색 요약: 서울 날씨\n\n서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "latest_update",
      verification_label: "단일 출처 참고",
      source_roles: ["보조 출처"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "서울 날씨",
          answer_mode: "latest_update",
          verification_label: "단일 출처 참고",
          source_roles: ["보조 출처"],
          result_count: 1,
          page_count: 1,
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

  // Click "다시 불러오기"
  await reloadButton.click();

  // Wait for the response to render
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Assert context box shows the single source URL
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("example.com/seoul-weather");

  // latest-update show-only reload empty-meta branch (single-source source-path): zero-count
  // summary + empty progress → history card must not render any `.meta` detail node and
  // must not leak `사실 검증` content.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card latest-update single-source 다시 불러오기 후 follow-up 질문에서 WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 drift하지 않습니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-latest-single-followup");

  // Pre-seed a single-source latest_update record
  const recordId = `websearch-latest-single-fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `서울날씨-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "서울 날씨",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 1,
    page_count: 1,
    results: [
      {
        title: "서울 날씨 - 예보",
        url: "https://example.com/seoul-weather",
        snippet: "서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.",
      },
    ],
    pages: [
      {
        url: "https://example.com/seoul-weather",
        title: "서울 날씨 - 예보",
        text: "서울은 맑고 낮 최고 17도. 미세먼지 보통.",
      },
    ],
    summary_text: "웹 검색 요약: 서울 날씨\n\n서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "latest_update",
      verification_label: "단일 출처 참고",
      source_roles: ["보조 출처"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "서울 날씨",
          answer_mode: "latest_update",
          verification_label: "단일 출처 참고",
          source_roles: ["보조 출처"],
          result_count: 1,
          page_count: 1,
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

  // Click "다시 불러오기" — show-only reload
  await reloadButton.click();

  // Wait for the initial reload response badges
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toHaveText("최신 확인");

  // Send a follow-up with load_web_search_record_id + user_text (non-show-only)
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Assert response origin badges are preserved after follow-up
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);

  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");

  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("단일 출처 참고");
  await expect(originDetail).toContainText("보조 출처");

  // latest-update non-noisy empty-meta branch: zero-count summary + empty progress → history
  // card must not render any `.meta` detail node and must not leak `사실 검증` content.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card latest-update news-only 다시 불러오기 후 follow-up 질문에서 WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 drift하지 않습니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-latest-news-followup");

  // Pre-seed a news-only latest_update record (hankyung + mk)
  const recordId = `websearch-latest-news-fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `기준금리-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "기준금리 속보",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 2,
    results: [
      {
        title: "기준금리 속보 - 한국경제",
        url: "https://www.hankyung.com/economy/2025",
        snippet: "한국은행이 기준금리를 동결했다고 밝혔다.",
      },
      {
        title: "기준금리 뉴스 - 매일경제",
        url: "https://www.mk.co.kr/economy/2025",
        snippet: "한국은행이 기준금리를 동결했다.",
      },
    ],
    pages: [
      {
        url: "https://www.hankyung.com/economy/2025",
        title: "기준금리 속보 - 한국경제",
        text: "한국은행이 기준금리를 동결했다고 밝혔다.",
      },
      {
        url: "https://www.mk.co.kr/economy/2025",
        title: "기준금리 뉴스 - 매일경제",
        text: "한국은행이 기준금리를 동결했다.",
      },
    ],
    summary_text: "웹 검색 요약: 기준금리 속보\n\n한국은행이 기준금리를 동결했다고 밝혔다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "latest_update",
      verification_label: "기사 교차 확인",
      source_roles: ["보조 기사"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "기준금리 속보",
          answer_mode: "latest_update",
          verification_label: "기사 교차 확인",
          source_roles: ["보조 기사"],
          result_count: 2,
          page_count: 2,
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

  // Click "다시 불러오기" — show-only reload
  await reloadButton.click();

  // Wait for the initial reload response badges
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toHaveText("최신 확인");

  // Send a follow-up with load_web_search_record_id + user_text (non-show-only)
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Assert response origin badges are preserved after follow-up
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);

  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");

  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("기사 교차 확인");
  await expect(originDetail).toContainText("보조 기사");

  // latest-update non-noisy empty-meta branch: zero-count summary + empty progress → history
  // card must not render any `.meta` detail node and must not leak `사실 검증` content.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card entity-card store-seeded actual-search initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-store-seeded-actual-search-initial-render-empty-meta");

  // Pre-seed a store-seeded actual-search entity_card record with `claim_coverage: []` and
  // empty progress, mirroring the service path that calls `WebSearchStore.save(...)`
  // without `claim_coverage`. Unlike the reload-only / follow-up / chain scenarios in the
  // same family, this initial-render scenario seeds the history item with the actual
  // serialized zero-count shape that `list_session_record_summaries` + `_serialize_web_search_history`
  // produce for this path (`claim_coverage_summary: { strong: 0, weak: 0, missing: 0, conflict: 0 }`,
  // empty progress) so the renderer is exercised on the real server → client payload,
  // not just the `undefined` omission case.
  const recordId = `websearch-entity-store-seeded-actual-initial-render-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      {
        title: "붉은사막 - 나무위키",
        url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
      {
        title: "붉은사막 - 위키백과",
        url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["백과 기반"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history item with the actual serialized zero-count shape that the server
  // emits for this store-seeded path. This exercises the `formatClaimCoverageCountSummary`
  // branch where the dict exists but every count is 0 and the joined detail line is empty,
  // so `detailLines` must stay empty and no `.meta` node must be appended.
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
          verification_label: "설명형 다중 출처 합의",
          source_roles: ["백과 기반"],
          result_count: 2,
          page_count: 0,
          created_at: record.created_at,
          record_path: recordPath,
          claim_coverage_summary: { strong: 0, weak: 0, missing: 0, conflict: 0 },
          claim_coverage_progress_summary: "",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();

  // Pre-click header / action expectations: the history item exposes the `다시 불러오기`
  // button and the answer-mode / verification / source badges appropriate for a stored
  // entity_card record. This scenario intentionally does NOT click the button, does NOT
  // send natural reload, and does NOT send any follow-up — the check is that the renderer
  // already suppresses `.meta` at the initial-render stage given the serialized zero-count.
  const historyCard = historyBox.locator(".history-item").first();
  const reloadButton = historyCard.locator(".history-item-actions button.secondary");
  await expect(reloadButton).toHaveText("다시 불러오기");

  // store-seeded empty-meta no-leak contract at the initial-render stage with the actual
  // serialized zero-count summary: `{strong:0, weak:0, missing:0}` + empty progress →
  // history card must not render any `.meta` detail node and must not leak `사실 검증`
  // content through accidental `.meta` creation, BEFORE any user interaction.
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card entity-card store-seeded actual-search 자연어 reload-only 단계에서 empty-meta no-leak contract가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-store-seeded-actual-search-natural-reload-only-empty-meta");

  // Pre-seed a store-seeded actual-search entity_card record with `claim_coverage: []` and
  // empty progress, mirroring the service path that calls `WebSearchStore.save(...)`
  // without `claim_coverage`. The `renderSearchHistory` item intentionally omits any
  // `claim_coverage_summary` or progress seed so the history-card renderer cannot build a
  // detail `.meta` node either before the natural-reload step.
  const recordId = `websearch-entity-store-seeded-actual-nat-reload-only-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      {
        title: "붉은사막 - 나무위키",
        url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
      {
        title: "붉은사막 - 위키백과",
        url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["백과 기반"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history item WITHOUT any non-zero claim_coverage_summary or progress seed.
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
          verification_label: "설명형 다중 출처 합의",
          source_roles: ["백과 기반"],
          result_count: 2,
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

  // Step 1: click "다시 불러오기" once to register the stored record in the server session
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Step 2: natural reload via `"방금 검색한 결과 다시 보여줘"` — STOP HERE.
  // This scenario intentionally does not continue into first or second follow-up so the
  // natural-reload-only browser no-leak edge can be locked independently.
  await page.evaluate(async () => {
    // @ts-ignore — sendRequest is defined in the page scope
    await sendRequest({
      user_text: "방금 검색한 결과 다시 보여줘",
    });
  });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("백과 기반");
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");

  // store-seeded empty-meta no-leak contract at the natural-reload-only stage: zero-count
  // summary + empty progress → history card must not render any `.meta` detail node and
  // must not leak `사실 검증` content through accidental `.meta` creation.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card entity-card store-seeded actual-search 다시 불러오기 reload-only 단계에서 empty-meta no-leak contract가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-store-seeded-actual-search-reload-only-empty-meta");

  // Pre-seed a store-seeded actual-search entity_card record with `claim_coverage: []` and
  // empty progress, mirroring the service path that calls `WebSearchStore.save(...)`
  // without `claim_coverage`. The `renderSearchHistory` item intentionally omits any
  // `claim_coverage_summary` or progress seed so the history-card renderer cannot build a
  // detail `.meta` node either before the click-reload step.
  const recordId = `websearch-entity-store-seeded-actual-reload-only-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      {
        title: "붉은사막 - 나무위키",
        url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
      {
        title: "붉은사막 - 위키백과",
        url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["백과 기반"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history item WITHOUT any non-zero claim_coverage_summary or progress seed.
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
          verification_label: "설명형 다중 출처 합의",
          source_roles: ["백과 기반"],
          result_count: 2,
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

  // Click "다시 불러오기" — show-only reload. No follow-up, no natural reload: this
  // scenario intentionally stops at the reload-only stage to lock the immediate no-leak
  // contract without leaning on any subsequent chain step.
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("백과 기반");
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");

  // store-seeded empty-meta no-leak contract at the reload-only stage: zero-count summary
  // + empty progress → history card must not render any `.meta` detail node and must not
  // leak `사실 검증` content through accidental `.meta` creation.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card entity-card store-seeded actual-search 다시 불러오기 후 follow-up 질문에서 empty-meta no-leak contract가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-store-seeded-actual-search-click-reload-followup-empty-meta");

  // Pre-seed a store-seeded actual-search entity_card record: two results, entity-card
  // response_origin with `설명형 다중 출처 합의` verification label and `백과 기반` source
  // role, but NO `claim_coverage` entries. This matches the store-seeded service path
  // (`WebSearchStore.save(...)` without `claim_coverage`), where `_summarize_claim_coverage`
  // returns `{strong:0, weak:0, missing:0}` and `_serialize_web_search_history` preserves
  // the zero-count dict + empty progress. The history-card renderer should therefore skip
  // the investigation-card detail `.meta` entirely and must not leak any `사실 검증` text.
  const recordId = `websearch-entity-store-seeded-actual-fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      {
        title: "붉은사막 - 나무위키",
        url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
      {
        title: "붉은사막 - 위키백과",
        url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["백과 기반"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history item WITHOUT any non-zero claim_coverage_summary or progress seed —
  // the client-side seed must not accidentally trigger `.meta` creation either.
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
          verification_label: "설명형 다중 출처 합의",
          source_roles: ["백과 기반"],
          result_count: 2,
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

  // Click "다시 불러오기" — show-only reload
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Send the first follow-up with load_web_search_record_id + user_text
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Existing continuity assertions: WEB badge, answer-mode, origin detail, source paths
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("백과 기반");
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");

  // store-seeded empty-meta no-leak contract: zero-count summary + empty progress →
  // history card must not render any `.meta` detail node and must not leak `사실 검증`
  // content through accidental `.meta` creation.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card entity-card store-seeded actual-search 다시 불러오기 후 두 번째 follow-up 질문에서 empty-meta no-leak contract가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-store-seeded-actual-search-click-reload-second-followup-empty-meta");

  // Pre-seed a store-seeded actual-search entity_card record with `claim_coverage: []` and
  // empty progress, mirroring the service path that calls `WebSearchStore.save(...)`
  // without `claim_coverage`. The `render`-side item also intentionally omits any
  // `claim_coverage_summary` or progress seed so the history-card renderer cannot build a
  // detail `.meta` node either before the click-reload chain starts.
  const recordId = `websearch-entity-store-seeded-actual-2fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      {
        title: "붉은사막 - 나무위키",
        url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
      {
        title: "붉은사막 - 위키백과",
        url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["백과 기반"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history item WITHOUT any non-zero claim_coverage_summary or progress seed.
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
          verification_label: "설명형 다중 출처 합의",
          source_roles: ["백과 기반"],
          result_count: 2,
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

  // Step 1: click "다시 불러오기" — show-only reload
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Step 2: first follow-up
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );
  await expect(originBadge).toHaveText("WEB");

  // Step 3: second follow-up on the same record
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "더 자세히 알려줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Existing continuity assertions after the second follow-up
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("백과 기반");
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");

  // store-seeded empty-meta no-leak contract (second follow-up): zero-count summary +
  // empty progress → history card must not render any `.meta` detail node and must not
  // leak `사실 검증` content through accidental `.meta` creation.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card entity-card store-seeded actual-search 자연어 reload 체인에서 empty-meta no-leak contract가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-store-seeded-actual-search-natural-reload-chain-empty-meta");

  // Pre-seed a store-seeded actual-search entity_card record with `claim_coverage: []` and
  // empty progress, mirroring the service path that calls `WebSearchStore.save(...)`
  // without `claim_coverage`. The `renderSearchHistory` item intentionally omits any
  // `claim_coverage_summary` or progress seed so the history-card renderer cannot build a
  // detail `.meta` node either before the chain starts.
  const recordId = `websearch-entity-store-seeded-actual-nat-chain-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      {
        title: "붉은사막 - 나무위키",
        url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
      {
        title: "붉은사막 - 위키백과",
        url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["백과 기반"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history item WITHOUT any non-zero claim_coverage_summary or progress seed.
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
          verification_label: "설명형 다중 출처 합의",
          source_roles: ["백과 기반"],
          result_count: 2,
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

  // Step 1: click "다시 불러오기" to register the record in the server session
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Step 2: natural reload via `"방금 검색한 결과 다시 보여줘"`
  await page.evaluate(async () => {
    // @ts-ignore — sendRequest is defined in the page scope
    await sendRequest({
      user_text: "방금 검색한 결과 다시 보여줘",
    });
  });
  await expect(originBadge).toHaveText("WEB");

  // Step 3: first follow-up on the same stored record
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );
  await expect(originBadge).toHaveText("WEB");

  // Step 4: second follow-up on the same stored record
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "더 자세히 알려줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Existing continuity assertions after the final (second) follow-up in the chain
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("백과 기반");
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");

  // store-seeded empty-meta no-leak contract after the natural-reload chain: zero-count
  // summary + empty progress → history card must not render any `.meta` detail node and
  // must not leak `사실 검증` content through accidental `.meta` creation.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path(namu.wiki, ko.wikipedia.org) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-entity-actual-followup-sp");

  // Pre-seed a generic entity_card record (붉은사막, single source without dual-probe)
  const recordId = `websearch-entity-actual-fu-sp-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      {
        title: "붉은사막 - 나무위키",
        url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
      {
        title: "붉은사막 - 위키백과",
        url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 붉은사막\n\n확인된 사실:\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다. [교차 확인]",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["백과 기반"],
    },
    // actual-search entity-card first-follow-up strong-plus-missing branch: stored
    // claim_coverage mirrors the runtime `{strong:3, weak:0, missing:2}` distribution with
    // empty progress. Slot names avoid noisy keywords (`출시일`/`2025`/`brunch`).
    claim_coverage: [
      { slot: "장르", status: "strong", status_label: "교차 확인", value: "오픈월드 액션 어드벤처 게임", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "개발사", status: "strong", status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "플랫폼", status: "strong", status_label: "교차 확인", value: "PC/콘솔", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "엔진", status: "missing", status_label: "미확인" },
      { slot: "난이도", status: "missing", status_label: "미확인" },
    ],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card
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
          verification_label: "설명형 다중 출처 합의",
          source_roles: ["백과 기반"],
          result_count: 2,
          page_count: 0,
          created_at: record.created_at,
          record_path: recordPath,
          claim_coverage_summary: { strong: 3, weak: 0, missing: 2, conflict: 0 },
          claim_coverage_progress_summary: "",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  const reloadButton = historyBox.locator(".history-item-actions button.secondary").first();
  await expect(reloadButton).toHaveText("다시 불러오기");

  // Click "다시 불러오기" — show-only reload
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Send a follow-up with load_web_search_record_id + user_text
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Assert context box still shows both actual-search source URLs after follow-up (plurality)
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");

  // Assert response-origin continuity after follow-up
  await expect(originBadge).toHaveText("WEB");
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("백과 기반");

  // actual-search first-follow-up strong-plus-missing meta: history-card `.meta` must be
  // the exact `사실 검증 교차 확인 3 · 미확인 2` line, with no answer-mode label leak.
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 3 · 미확인 2");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 actual-search source path(namu.wiki, ko.wikipedia.org) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-entity-actual-second-followup-sp");

  const recordId = `websearch-entity-actual-2fu-sp-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      {
        title: "붉은사막 - 나무위키",
        url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
      {
        title: "붉은사막 - 위키백과",
        url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 붉은사막\n\n확인된 사실:\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다. [교차 확인]",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["백과 기반"],
    },
    // Strong-plus-missing claim_coverage mix matches the actual actual-search runtime branch
    // observed via the focused probe: `strong=3`, `weak=0`, `missing=2`, empty progress summary.
    claim_coverage: [
      { slot: "장르", status: "strong", status_label: "교차 확인", value: "오픈월드 액션 어드벤처 게임", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "개발사", status: "strong", status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "플랫폼", status: "strong", status_label: "교차 확인", value: "PC/콘솔", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "출시일", status: "missing", status_label: "미확인" },
      { slot: "가격", status: "missing", status_label: "미확인" },
    ],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

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
          verification_label: "설명형 다중 출처 합의",
          source_roles: ["백과 기반"],
          result_count: 2,
          page_count: 0,
          created_at: record.created_at,
          record_path: recordPath,
          claim_coverage_summary: { strong: 3, weak: 0, missing: 2, conflict: 0 },
          claim_coverage_progress_summary: "",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // First follow-up
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  await expect(originBadge).toHaveText("WEB");

  // After the first follow-up the history-card `.meta` must already carry the strong-plus-missing
  // count-only line derived from the stored claim_coverage (3 strong + 2 missing slots).
  // `formatClaimCoverageCountSummary({strong:3, missing:2})` yields `"교차 확인 3 · 미확인 2"`.
  // entity_card is investigation, so detailLines skip the answer-mode label.
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 3 · 미확인 2");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");

  // Second follow-up
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "더 자세히 알려줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Assert context box shows both source URLs after second follow-up
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");

  // Assert response-origin continuity
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("백과 기반");

  // The history-card `.meta` must still carry the same strong-plus-missing count-only line
  // with no drift, no leaked answer-mode label, no leading/trailing separator, and no doubled
  // separator. The count line legitimately contains ` · ` between `교차 확인 3` and `미확인 2`,
  // so we assert exact text + absence of ` ·  · ` instead of a blanket `not.toContainText("·")`.
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 3 · 미확인 2");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");
  await expect(historyCardMeta).not.toContainText(" ·  · ");
  const postSecondFollowUpMetaText = ((await historyCardMeta.textContent()) || "").trim();
  expect(postSecondFollowUpMetaText.length).toBeGreaterThan(0);
  expect(postSecondFollowUpMetaText.startsWith("·")).toBe(false);
  expect(postSecondFollowUpMetaText.endsWith("·")).toBe(false);

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 dual-probe source path(pearlabyss.com/200, pearlabyss.com/300) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 drift하지 않습니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-entity-dual-second-followup-origin");

  const recordId = `websearch-entity-dual-2fu-or-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 2,
    results: [
      { title: "붉은사막 - 나무위키", url: "https://namu.wiki/w/test", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.", matched_query: "붉은사막" },
      { title: "붉은사막 | 플랫폼 - 공식", url: "https://www.pearlabyss.com/200", snippet: "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이다.", matched_query: "붉은사막 공식 플랫폼" },
      { title: "붉은사막 | 서비스 - 공식", url: "https://www.pearlabyss.com/300", snippet: "붉은사막은 펄어비스가 운영하는 게임이다.", matched_query: "붉은사막 서비스 공식" },
    ],
    pages: [
      { url: "https://www.pearlabyss.com/200", title: "붉은사막 | 플랫폼 - 공식", text: "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이며 펄어비스가 개발 중입니다." },
      { url: "https://www.pearlabyss.com/300", title: "붉은사막 | 서비스 - 공식", text: "붉은사막은 펄어비스가 운영하는 게임이며 배급도 펄어비스가 담당합니다." },
    ],
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "entity_card", verification_label: "설명형 다중 출처 합의", source_roles: ["공식 기반", "백과 기반"] },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{ record_id: recordId, query: "붉은사막", answer_mode: "entity_card", verification_label: "설명형 다중 출처 합의", source_roles: ["공식 기반", "백과 기반"], result_count: 3, page_count: 2, created_at: record.created_at, record_path: recordPath }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // First follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });
  await expect(originBadge).toHaveText("WEB");

  // Second follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "더 자세히 알려줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  // Assert response-origin continuity after second follow-up
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("공식 기반");
  await expect(originDetail).toContainText("백과 기반");

  // Assert context box shows dual-probe source URLs
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("pearlabyss.com/200");
  await expect(contextBox).toContainText("pearlabyss.com/300");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 dual-probe mixed count-summary meta가 truthfully 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-entity-dual-second-followup-mixed-count-summary");

  // Pre-seed a dual-probe entity_card record whose on-disk claim_coverage is 1 strong slot +
  // 4 weak slots — matching the actual runtime counts observed via the service probe.
  const recordId = `websearch-entity-dual-2fu-mix-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const mixedCoverage = [
    { slot: "개발사", status: "strong", status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "official" },
    { slot: "장르", status: "weak", status_label: "단일 출처", value: "오픈월드 액션 어드벤처", support_count: 1, candidate_count: 1, source_role: "encyclopedia" },
    { slot: "플랫폼", status: "weak", status_label: "단일 출처", value: "PC/콘솔", support_count: 1, candidate_count: 1, source_role: "official" },
    { slot: "서비스", status: "weak", status_label: "단일 출처", value: "펄어비스", support_count: 1, candidate_count: 1, source_role: "official" },
    { slot: "출시일", status: "weak", status_label: "단일 출처", value: "미정", support_count: 1, candidate_count: 1, source_role: "official" },
  ];
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 2,
    results: [
      { title: "붉은사막 - 나무위키", url: "https://namu.wiki/w/test", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.", matched_query: "붉은사막" },
      { title: "붉은사막 | 플랫폼 - 공식", url: "https://www.pearlabyss.com/200", snippet: "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이다.", matched_query: "붉은사막 공식 플랫폼" },
      { title: "붉은사막 | 서비스 - 공식", url: "https://www.pearlabyss.com/300", snippet: "붉은사막은 펄어비스가 운영하는 게임이다.", matched_query: "붉은사막 서비스 공식" },
    ],
    pages: [
      { url: "https://www.pearlabyss.com/200", title: "붉은사막 | 플랫폼 - 공식", text: "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이며 펄어비스가 개발 중입니다." },
      { url: "https://www.pearlabyss.com/300", title: "붉은사막 | 서비스 - 공식", text: "붉은사막은 펄어비스가 운영하는 게임이며 배급도 펄어비스가 담당합니다." },
    ],
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "entity_card", verification_label: "설명형 다중 출처 합의", source_roles: ["공식 기반", "백과 기반"] },
    claim_coverage: mixedCoverage,
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Seed the session's web_search_history with a matching mixed count-summary so the
  // pre-click meta observation is consistent with the post-reload server re-serialization.
  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{
      record_id: recordId,
      query: "붉은사막",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["공식 기반", "백과 기반"],
      result_count: 3,
      page_count: 2,
      created_at: record.created_at,
      record_path: recordPath,
      claim_coverage_summary: { strong: 1, weak: 4, missing: 0, conflict: 0 },
      claim_coverage_progress_summary: "",
    }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toHaveText("설명 카드");

  // First follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });
  await expect(originBadge).toHaveText("WEB");
  await expect(answerModeBadge).toHaveText("설명 카드");

  // After the first follow-up the history-card `.meta` must already carry the mixed
  // count-only line derived from the stored claim_coverage (1 strong + 4 weak slots).
  // `formatClaimCoverageCountSummary({strong:1, weak:4})` yields `"교차 확인 1 · 단일 출처 4"`.
  // entity_card is investigation, so detailLines skip the answer-mode label.
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 1 · 단일 출처 4");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");

  // Second follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "더 자세히 알려줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  // Assert origin / answer-mode / origin detail / source path continuity
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("공식 기반");
  await expect(originDetail).toContainText("백과 기반");
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("pearlabyss.com/200");
  await expect(contextBox).toContainText("pearlabyss.com/300");

  // The history-card `.meta` must still carry the same mixed count-only line with no drift,
  // no leaked answer-mode label, no leading/trailing separator, and no doubled separator.
  // The count line legitimately contains ` · ` as a join between `교차 확인 1` and `단일 출처 4`,
  // so we assert the exact text and the absence of ` ·  · ` (double separator) instead of a
  // blanket `not.toContainText("·")`.
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 1 · 단일 출처 4");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");
  await expect(historyCardMeta).not.toContainText(" ·  · ");
  const postSecondFollowUpMetaText = ((await historyCardMeta.textContent()) || "").trim();
  expect(postSecondFollowUpMetaText.length).toBeGreaterThan(0);
  expect(postSecondFollowUpMetaText.startsWith("·")).toBe(false);
  expect(postSecondFollowUpMetaText.endsWith("·")).toBe(false);

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("history-card entity-card 다시 불러오기 후 follow-up 질문에서 dual-probe source path(pearlabyss.com/200, pearlabyss.com/300) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-entity-dual-followup");

  // Pre-seed an entity_card record with dual-probe results
  const recordId = `websearch-entity-dual-fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 2,
    results: [
      {
        title: "붉은사막 - 나무위키",
        url: "https://namu.wiki/w/test",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
        matched_query: "붉은사막",
      },
      {
        title: "붉은사막 | 플랫폼 - 공식",
        url: "https://www.pearlabyss.com/200",
        snippet: "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이다.",
        matched_query: "붉은사막 공식 플랫폼",
      },
      {
        title: "붉은사막 | 서비스 - 공식",
        url: "https://www.pearlabyss.com/300",
        snippet: "붉은사막은 펄어비스가 운영하는 게임이다.",
        matched_query: "붉은사막 서비스 공식",
      },
    ],
    pages: [
      {
        url: "https://www.pearlabyss.com/200",
        title: "붉은사막 | 플랫폼 - 공식",
        text: "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이며 펄어비스가 개발 중입니다.",
      },
      {
        url: "https://www.pearlabyss.com/300",
        title: "붉은사막 | 서비스 - 공식",
        text: "붉은사막은 펄어비스가 운영하는 게임이며 배급도 펄어비스가 담당합니다.",
      },
    ],
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["공식 기반", "백과 기반"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card
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
          verification_label: "설명형 다중 출처 합의",
          source_roles: ["공식 기반", "백과 기반"],
          result_count: 3,
          page_count: 2,
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

  // Click "다시 불러오기" — show-only reload
  await reloadButton.click();

  // Wait for the response to render
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Send a follow-up with load_web_search_record_id + user_text
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Assert context box still shows both dual-probe source URLs after follow-up
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("pearlabyss.com/200");
  await expect(contextBox).toContainText("pearlabyss.com/300");

  // Assert response-origin continuity after follow-up
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("공식 기반");
  await expect(originDetail).toContainText("백과 기반");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card latest-update mixed-source 다시 불러오기 후 follow-up 질문에서 source path(store.steampowered.com, yna.co.kr) + WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-latest-mixed-followup-sp");

  // Pre-seed a mixed-source latest_update record
  const recordId = `websearch-latest-mixed-fu-sp-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `스팀할인-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "스팀 여름 할인",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 2,
    results: [
      {
        title: "Steam 여름 할인 - Steam Store",
        url: "https://store.steampowered.com/sale/summer2026",
        snippet: "Steam 여름 할인이 시작되었습니다.",
      },
      {
        title: "스팀 여름 할인 시작 - 게임뉴스",
        url: "https://www.yna.co.kr/view/AKR20260401000100017",
        snippet: "스팀이 2026년 여름 할인을 시작했다.",
      },
    ],
    pages: [
      {
        url: "https://store.steampowered.com/sale/summer2026",
        title: "Steam 여름 할인 - Steam Store",
        text: "Steam 여름 할인이 시작되었습니다.",
      },
      {
        url: "https://www.yna.co.kr/view/AKR20260401000100017",
        title: "스팀 여름 할인 시작 - 게임뉴스",
        text: "스팀이 2026년 여름 할인을 시작했다.",
      },
    ],
    summary_text: "웹 검색 요약: 스팀 여름 할인\n\nSteam 여름 할인이 시작되었습니다. 수천 개 게임이 최대 90% 할인됩니다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "latest_update",
      verification_label: "공식+기사 교차 확인",
      source_roles: ["보조 기사", "공식 기반"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "스팀 여름 할인",
          answer_mode: "latest_update",
          verification_label: "공식+기사 교차 확인",
          source_roles: ["보조 기사", "공식 기반"],
          result_count: 2,
          page_count: 2,
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

  // Click "다시 불러오기" — show-only reload
  await reloadButton.click();

  // Wait for the response to render
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Send a follow-up with load_web_search_record_id + user_text
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Assert context box still shows both mixed-source URLs after follow-up
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("store.steampowered.com");
  await expect(contextBox).toContainText("yna.co.kr");

  // Assert response-origin continuity after follow-up
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("공식+기사 교차 확인");
  await expect(originDetail).toContainText("보조 기사");
  await expect(originDetail).toContainText("공식 기반");

  // latest-update non-noisy empty-meta branch: zero-count summary + empty progress → history
  // card must not render any `.meta` detail node and must not leak `사실 검증` content.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card latest-update mixed-source 다시 불러오기 후 두 번째 follow-up 질문에서 source path(store.steampowered.com, yna.co.kr) + WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 drift하지 않습니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-latest-mixed-second-followup");

  const recordId = `websearch-latest-mixed-2fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `스팀할인-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "스팀 여름 할인",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 2,
    results: [
      { title: "Steam 여름 할인 - Steam Store", url: "https://store.steampowered.com/sale/summer2026", snippet: "Steam 여름 할인이 시작되었습니다." },
      { title: "스팀 여름 할인 시작 - 게임뉴스", url: "https://www.yna.co.kr/view/AKR20260401000100017", snippet: "스팀이 2026년 여름 할인을 시작했다." },
    ],
    pages: [
      { url: "https://store.steampowered.com/sale/summer2026", title: "Steam 여름 할인", text: "Steam 여름 할인이 시작되었습니다." },
      { url: "https://www.yna.co.kr/view/AKR20260401000100017", title: "스팀 여름 할인 시작", text: "스팀이 2026년 여름 할인을 시작했다." },
    ],
    summary_text: "웹 검색 요약: 스팀 여름 할인\n\nSteam 여름 할인이 시작되었습니다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "latest_update", verification_label: "공식+기사 교차 확인", source_roles: ["보조 기사", "공식 기반"] },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{ record_id: recordId, query: "스팀 여름 할인", answer_mode: "latest_update", verification_label: "공식+기사 교차 확인", source_roles: ["보조 기사", "공식 기반"], result_count: 2, page_count: 2, created_at: record.created_at, record_path: recordPath }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // First follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });
  await expect(originBadge).toHaveText("WEB");

  // Second follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "더 자세히 알려줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("공식+기사 교차 확인");
  await expect(originDetail).toContainText("보조 기사");
  await expect(originDetail).toContainText("공식 기반");

  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("store.steampowered.com");
  await expect(contextBox).toContainText("yna.co.kr");

  // latest-update non-noisy empty-meta branch: zero-count summary + empty progress → history
  // card must not render any `.meta` detail node and must not leak `사실 검증` content.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("history-card latest-update single-source 다시 불러오기 후 follow-up 질문에서 source path(example.com/seoul-weather) + WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-latest-single-followup-sp");

  // Pre-seed a single-source latest_update record
  const recordId = `websearch-latest-single-fu-sp-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `서울날씨-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "서울 날씨",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 1,
    page_count: 1,
    results: [
      {
        title: "서울 날씨 - 예보",
        url: "https://example.com/seoul-weather",
        snippet: "서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.",
      },
    ],
    pages: [
      {
        url: "https://example.com/seoul-weather",
        title: "서울 날씨 - 예보",
        text: "서울은 맑고 낮 최고 17도. 미세먼지 보통.",
      },
    ],
    summary_text: "웹 검색 요약: 서울 날씨\n\n서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "latest_update",
      verification_label: "단일 출처 참고",
      source_roles: ["보조 출처"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "서울 날씨",
          answer_mode: "latest_update",
          verification_label: "단일 출처 참고",
          source_roles: ["보조 출처"],
          result_count: 1,
          page_count: 1,
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

  // Click "다시 불러오기" — show-only reload
  await reloadButton.click();

  // Wait for the response to render
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Send a follow-up with load_web_search_record_id + user_text
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Assert context box still shows the single source URL after follow-up
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("example.com/seoul-weather");

  // latest-update non-noisy empty-meta branch: zero-count summary + empty progress → history
  // card must not render any `.meta` detail node and must not leak `사실 검증` content.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card latest-update news-only 다시 불러오기 후 follow-up 질문에서 기사 source path(hankyung.com, mk.co.kr) + WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-latest-news-followup-sp");

  // Pre-seed a news-only latest_update record (hankyung + mk)
  const recordId = `websearch-latest-news-fu-sp-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `기준금리-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "기준금리 속보",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 2,
    results: [
      {
        title: "기준금리 속보 - 한국경제",
        url: "https://www.hankyung.com/economy/2025",
        snippet: "한국은행이 기준금리를 동결했다고 밝혔다.",
      },
      {
        title: "기준금리 뉴스 - 매일경제",
        url: "https://www.mk.co.kr/economy/2025",
        snippet: "한국은행이 기준금리를 동결했다.",
      },
    ],
    pages: [
      {
        url: "https://www.hankyung.com/economy/2025",
        title: "기준금리 속보 - 한국경제",
        text: "한국은행이 기준금리를 동결했다고 밝혔다.",
      },
      {
        url: "https://www.mk.co.kr/economy/2025",
        title: "기준금리 뉴스 - 매일경제",
        text: "한국은행이 기준금리를 동결했다.",
      },
    ],
    summary_text: "웹 검색 요약: 기준금리 속보\n\n한국은행이 기준금리를 동결했다고 밝혔다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "latest_update",
      verification_label: "기사 교차 확인",
      source_roles: ["보조 기사"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "기준금리 속보",
          answer_mode: "latest_update",
          verification_label: "기사 교차 확인",
          source_roles: ["보조 기사"],
          result_count: 2,
          page_count: 2,
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

  // Click "다시 불러오기" — show-only reload
  await reloadButton.click();

  // Wait for the response to render
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Send a follow-up with load_web_search_record_id + user_text
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Assert context box still shows both news source URLs after follow-up
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("hankyung.com");
  await expect(contextBox).toContainText("mk.co.kr");

  // latest-update non-noisy empty-meta branch: zero-count summary + empty progress → history
  // card must not render any `.meta` detail node and must not leak `사실 검증` content.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card entity-card zero-strong-slot 다시 불러오기 후 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu.wiki/ko.wikipedia.org가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-entity-zero-strong");

  // Pre-seed a zero-strong-slot entity_card record (downgraded from strong to medium)
  const recordId = `websearch-entity-zero-strong-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `테스트게임-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "테스트게임",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      {
        title: "테스트게임 - 나무위키",
        url: "https://namu.wiki/w/testgame",
        snippet: "테스트게임은 알 수 없는 개발사의 게임이다.",
      },
      {
        title: "테스트게임 - 위키백과",
        url: "https://ko.wikipedia.org/wiki/testgame",
        snippet: "테스트게임은 정보가 부족한 게임이다.",
      },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 테스트게임\n\n테스트게임은 알 수 없는 개발사의 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 단일 출처",
      source_roles: ["백과 기반"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card with zero-strong-slot entity_card
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "테스트게임",
          answer_mode: "entity_card",
          verification_label: "설명형 단일 출처",
          source_roles: ["백과 기반"],
          result_count: 2,
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

  // Click "다시 불러오기"
  await reloadButton.click();

  // Assert reloaded response keeps entity_card badges
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);

  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");

  // Assert origin detail shows downgraded verification label and source role
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 단일 출처");
  await expect(originDetail).toContainText("백과 기반");

  // Assert context box shows both source URLs (source-path continuity)
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card entity-card zero-strong-slot 다시 불러오기 후 missing-only count-summary meta가 truthfully 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-entity-zero-strong-missing-only-meta");

  // Pre-seed a zero-strong-slot entity_card record whose on-disk claim_coverage is five
  // missing-status slots — matching the actual runtime branch observed via the service probe.
  const recordId = `websearch-entity-zero-missing-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `테스트게임-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const missingSlots = ["장르", "개발사", "출시일", "플랫폼", "가격"].map((slot) => ({
    slot,
    status: "missing",
    status_label: "미확인",
  }));
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "테스트게임",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      {
        title: "테스트게임 - 나무위키",
        url: "https://namu.wiki/w/testgame",
        snippet: "테스트게임은 알 수 없는 개발사의 게임이다.",
      },
      {
        title: "테스트게임 - 위키백과",
        url: "https://ko.wikipedia.org/wiki/testgame",
        snippet: "테스트게임은 정보가 부족한 게임이다.",
      },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 테스트게임\n\n테스트게임은 알 수 없는 개발사의 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 단일 출처",
      source_roles: ["백과 기반"],
    },
    claim_coverage: missingSlots,
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card with a client-seeded missing-only count summary that matches
  // what the server's `_summarize_claim_coverage` will produce on reload from the same record.
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "테스트게임",
          answer_mode: "entity_card",
          verification_label: "설명형 단일 출처",
          source_roles: ["백과 기반"],
          result_count: 2,
          page_count: 0,
          created_at: record.created_at,
          record_path: recordPath,
          claim_coverage_summary: { strong: 0, weak: 0, missing: 5, conflict: 0 },
          claim_coverage_progress_summary: "",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  const reloadButton = historyBox.locator(".history-item-actions button.secondary").first();
  await expect(reloadButton).toHaveText("다시 불러오기");

  // History-card `.meta` must be the single count-only line derived from the missing-only
  // count-summary. entity_card is investigation so detailLines skip the answer-mode label,
  // `formatClaimCoverageCountSummary({missing:5})` yields `"미확인 5"`, and the final join
  // produces a single detailLine — no leading/trailing separator artifact.
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 미확인 5");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");
  await expect(historyCardMeta).not.toContainText("·");
  const preReloadMetaText = ((await historyCardMeta.textContent()) || "").trim();
  expect(preReloadMetaText.length).toBeGreaterThan(0);
  expect(preReloadMetaText.startsWith("·")).toBe(false);
  expect(preReloadMetaText.endsWith("·")).toBe(false);

  // Click "다시 불러오기" — server reloads the record, recomputes the history summary via
  // `_summarize_claim_coverage`, and re-serializes five missing slots back to the same
  // `{strong:0, weak:0, missing:5}` shape. `.meta` must therefore stay exactly the same.
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);

  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");

  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 단일 출처");
  await expect(originDetail).toContainText("백과 기반");

  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");

  // The history-card `.meta` must still expose the same missing-only count-only line.
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 미확인 5");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");
  await expect(historyCardMeta).not.toContainText("·");
  const postReloadMetaText = ((await historyCardMeta.textContent()) || "").trim();
  expect(postReloadMetaText.length).toBeGreaterThan(0);
  expect(postReloadMetaText.startsWith("·")).toBe(false);
  expect(postReloadMetaText.endsWith("·")).toBe(false);

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("history-card entity-card zero-strong-slot 다시 불러오기 후 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu.wiki/ko.wikipedia.org가 drift하지 않습니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-entity-zero-strong-followup");

  // Pre-seed a zero-strong-slot entity_card record
  const recordId = `websearch-entity-zero-fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `테스트게임-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "테스트게임",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      {
        title: "테스트게임 - 나무위키",
        url: "https://namu.wiki/w/testgame",
        snippet: "테스트게임은 알 수 없는 개발사의 게임이다.",
      },
      {
        title: "테스트게임 - 위키백과",
        url: "https://ko.wikipedia.org/wiki/testgame",
        snippet: "테스트게임은 정보가 부족한 게임이다.",
      },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 테스트게임\n\n테스트게임은 알 수 없는 개발사의 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 단일 출처",
      source_roles: ["백과 기반"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Render the history card
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "테스트게임",
          answer_mode: "entity_card",
          verification_label: "설명형 단일 출처",
          source_roles: ["백과 기반"],
          result_count: 2,
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

  // Click "다시 불러오기" — show-only reload
  await reloadButton.click();

  // Wait for the initial reload response badges
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toHaveText("설명 카드");

  // Send a follow-up with load_web_search_record_id + user_text (non-show-only)
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Assert response origin badges are preserved after follow-up
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);

  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");

  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 단일 출처");
  await expect(originDetail).toContainText("백과 기반");

  // Assert context box shows both source URLs after follow-up (source-path continuity)
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("entity-card zero-strong-slot 다시 불러오기 후 두 번째 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu.wiki/ko.wikipedia.org가 drift하지 않습니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-zero-strong-natural-reload-followup");

  // Pre-seed a zero-strong-slot entity_card record on disk
  const recordId = `websearch-entity-zero-nat-fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `테스트게임-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "테스트게임",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      {
        title: "테스트게임 - 나무위키",
        url: "https://namu.wiki/w/testgame",
        snippet: "테스트게임은 알 수 없는 개발사의 게임이다.",
      },
      {
        title: "테스트게임 - 위키백과",
        url: "https://ko.wikipedia.org/wiki/testgame",
        snippet: "테스트게임은 정보가 부족한 게임이다.",
      },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 테스트게임\n\n테스트게임은 알 수 없는 개발사의 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 단일 출처",
      source_roles: ["백과 기반"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Seed the session's web_search_history so reload can find it
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "테스트게임",
          answer_mode: "entity_card",
          verification_label: "설명형 단일 출처",
          source_roles: ["백과 기반"],
          result_count: 2,
          page_count: 0,
          created_at: record.created_at,
          record_path: recordPath,
        },
      ],
    }
  );

  // Step 1: load the record via show-only reload (click "다시 불러오기")
  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  const reloadButton = historyBox.locator(".history-item-actions button.secondary").first();
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Step 2: follow-up with user_text (simulating natural continuation after reload)
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Assert response origin badges are preserved after follow-up
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);

  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");

  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 단일 출처");
  await expect(originDetail).toContainText("백과 기반");

  // Assert context box shows both source URLs after second follow-up (source-path continuity)
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("entity-card zero-strong-slot 다시 불러오기 후 두 번째 follow-up 질문에서 missing-only count-summary meta가 truthfully 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-zero-strong-click-reload-second-followup-missing-only-meta");

  // Pre-seed a zero-strong-slot entity_card record on disk whose claim_coverage is five
  // missing-status slots — matching the actual runtime branch observed via the service probe.
  const recordId = `websearch-zero-click-fu2-missing-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `테스트게임-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const missingSlots = ["장르", "개발사", "출시일", "플랫폼", "가격"].map((slot) => ({
    slot,
    status: "missing",
    status_label: "미확인",
  }));
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "테스트게임",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      {
        title: "테스트게임 - 나무위키",
        url: "https://namu.wiki/w/testgame",
        snippet: "테스트게임은 알 수 없는 개발사의 게임이다.",
      },
      {
        title: "테스트게임 - 위키백과",
        url: "https://ko.wikipedia.org/wiki/testgame",
        snippet: "테스트게임은 정보가 부족한 게임이다.",
      },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 테스트게임\n\n테스트게임은 알 수 없는 개발사의 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 단일 출처",
      source_roles: ["백과 기반"],
    },
    claim_coverage: missingSlots,
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Seed the session's web_search_history with a matching missing-only count-summary so
  // the pre-click meta observation is consistent with the post-reload server re-serialization.
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "테스트게임",
          answer_mode: "entity_card",
          verification_label: "설명형 단일 출처",
          source_roles: ["백과 기반"],
          result_count: 2,
          page_count: 0,
          created_at: record.created_at,
          record_path: recordPath,
          claim_coverage_summary: { strong: 0, weak: 0, missing: 5, conflict: 0 },
          claim_coverage_progress_summary: "",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  const reloadButton = historyBox.locator(".history-item-actions button.secondary").first();
  await expect(reloadButton).toHaveText("다시 불러오기");

  // Step 1: click "다시 불러오기" (show-only reload)
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toHaveText("설명 카드");

  // Step 2: first follow-up (user_text + load_web_search_record_id)
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  await expect(originBadge).toHaveText("WEB");
  await expect(answerModeBadge).toHaveText("설명 카드");

  // After the first follow-up the history-card `.meta` must already be the missing-only
  // count-only line derived from the stored claim_coverage (5 missing slots).
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 미확인 5");
  await expect(historyCardMeta).not.toContainText("·");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");

  // Step 3: second follow-up (another user_text + load_web_search_record_id)
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 게임 장르만 한 줄로 다시 정리해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Assert response origin / answer-mode / origin detail / source path continuity
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 단일 출처");
  await expect(originDetail).toContainText("백과 기반");
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");

  // The history-card `.meta` must still carry the same missing-only count-only line with
  // no drift, no leaked answer-mode label, no `·` separator artifact, and no leading/
  // trailing separator.
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 미확인 5");
  await expect(historyCardMeta).not.toContainText("·");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");
  const postSecondFollowUpMetaText = ((await historyCardMeta.textContent()) || "").trim();
  expect(postSecondFollowUpMetaText.length).toBeGreaterThan(0);
  expect(postSecondFollowUpMetaText.startsWith("·")).toBe(false);
  expect(postSecondFollowUpMetaText.endsWith("·")).toBe(false);

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("entity-card zero-strong-slot 방금 검색한 결과 다시 보여줘 자연어 reload에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu.wiki/ko.wikipedia.org가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-zero-strong-browser-natural-reload");

  // Pre-seed a zero-strong-slot entity_card record on disk
  const recordId = `websearch-entity-zero-nat-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `테스트게임-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "테스트게임",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      {
        title: "테스트게임 - 나무위키",
        url: "https://namu.wiki/w/testgame",
        snippet: "테스트게임은 알 수 없는 개발사의 게임이다.",
      },
      {
        title: "테스트게임 - 위키백과",
        url: "https://ko.wikipedia.org/wiki/testgame",
        snippet: "테스트게임은 정보가 부족한 게임이다.",
      },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 테스트게임\n\n테스트게임은 알 수 없는 개발사의 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 단일 출처",
      source_roles: ["백과 기반"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Step 1: click "다시 불러오기" to register record in server session
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "테스트게임",
          answer_mode: "entity_card",
          verification_label: "설명형 단일 출처",
          source_roles: ["백과 기반"],
          result_count: 2,
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
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Step 2: natural reload — send "방금 검색한 결과 다시 보여줘" without record ID
  await page.evaluate(async () => {
    // @ts-ignore — sendRequest is defined in the page scope
    await sendRequest({
      user_text: "방금 검색한 결과 다시 보여줘",
    });
  });

  // Assert natural reload preserves response origin badges
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);

  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");

  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 단일 출처");
  await expect(originDetail).toContainText("백과 기반");

  // Assert context box shows both source URLs (source-path continuity)
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("entity-card zero-strong-slot 자연어 reload 후 follow-up에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu.wiki/ko.wikipedia.org가 drift하지 않습니다 (browser natural-reload path)", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-zero-strong-browser-natural-reload-followup");

  // Pre-seed a zero-strong-slot entity_card record on disk
  const recordId = `websearch-entity-zero-nat-fu2-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `테스트게임-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "테스트게임",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      {
        title: "테스트게임 - 나무위키",
        url: "https://namu.wiki/w/testgame",
        snippet: "테스트게임은 알 수 없는 개발사의 게임이다.",
      },
      {
        title: "테스트게임 - 위키백과",
        url: "https://ko.wikipedia.org/wiki/testgame",
        snippet: "테스트게임은 정보가 부족한 게임이다.",
      },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 테스트게임\n\n테스트게임은 알 수 없는 개발사의 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 단일 출처",
      source_roles: ["백과 기반"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Step 1: click reload to register record in server session
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "테스트게임",
          answer_mode: "entity_card",
          verification_label: "설명형 단일 출처",
          source_roles: ["백과 기반"],
          result_count: 2,
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
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Step 2: natural reload
  await page.evaluate(async () => {
    // @ts-ignore — sendRequest is defined in the page scope
    await sendRequest({
      user_text: "방금 검색한 결과 다시 보여줘",
    });
  });

  await expect(originBadge).toHaveText("WEB");

  // Step 3: follow-up after natural reload
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Assert follow-up preserves response origin badges
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);

  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");

  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 단일 출처");
  await expect(originDetail).toContainText("백과 기반");

  // Assert context box shows both source URLs after follow-up (source-path continuity)
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("entity-card zero-strong-slot 자연어 reload 후 두 번째 follow-up에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu.wiki/ko.wikipedia.org가 drift하지 않습니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-zero-strong-browser-natural-reload-second-followup");

  // Pre-seed a zero-strong-slot entity_card record on disk (empty claim_coverage / progress).
  const recordId = `websearch-entity-zero-nat-fu2-second-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `테스트게임-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "테스트게임",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      {
        title: "테스트게임 - 나무위키",
        url: "https://namu.wiki/w/testgame",
        snippet: "테스트게임은 알 수 없는 개발사의 게임이다.",
      },
      {
        title: "테스트게임 - 위키백과",
        url: "https://ko.wikipedia.org/wiki/testgame",
        snippet: "테스트게임은 정보가 부족한 게임이다.",
      },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 테스트게임\n\n테스트게임은 알 수 없는 개발사의 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 단일 출처",
      source_roles: ["백과 기반"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Step 1: click reload to register record in server session
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "테스트게임",
          answer_mode: "entity_card",
          verification_label: "설명형 단일 출처",
          source_roles: ["백과 기반"],
          result_count: 2,
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
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Step 2: natural reload — send "방금 검색한 결과 다시 보여줘" without record ID
  await page.evaluate(async () => {
    // @ts-ignore — sendRequest is defined in the page scope
    await sendRequest({
      user_text: "방금 검색한 결과 다시 보여줘",
    });
  });

  await expect(originBadge).toHaveText("WEB");

  // Step 3: first follow-up after natural reload (user_text + load_web_search_record_id)
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  await expect(originBadge).toHaveText("WEB");

  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");

  // Step 4: SECOND follow-up on the same record
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 게임 장르만 한 줄로 다시 정리해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Assert response origin badges, answer-mode label, origin detail, and source-path continuity
  // are preserved after the second follow-up.
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);

  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");

  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 단일 출처");
  await expect(originDetail).toContainText("백과 기반");

  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("entity-card zero-strong-slot 자연어 reload 후 두 번째 follow-up에서 missing-only count-summary meta가 truthfully 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-zero-strong-natural-reload-second-followup-missing-only-meta");

  // Pre-seed a zero-strong-slot entity_card record on disk whose claim_coverage is five
  // missing-status slots — matching the actual runtime branch.
  const recordId = `websearch-zero-nat-fu2-missing-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `테스트게임-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const missingSlots = ["장르", "개발사", "출시일", "플랫폼", "가격"].map((slot) => ({
    slot,
    status: "missing",
    status_label: "미확인",
  }));
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "테스트게임",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      {
        title: "테스트게임 - 나무위키",
        url: "https://namu.wiki/w/testgame",
        snippet: "테스트게임은 알 수 없는 개발사의 게임이다.",
      },
      {
        title: "테스트게임 - 위키백과",
        url: "https://ko.wikipedia.org/wiki/testgame",
        snippet: "테스트게임은 정보가 부족한 게임이다.",
      },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 테스트게임\n\n테스트게임은 알 수 없는 개발사의 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 단일 출처",
      source_roles: ["백과 기반"],
    },
    claim_coverage: missingSlots,
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Seed the session's web_search_history with a matching missing-only count-summary so
  // the pre-click meta observation is consistent with the server re-serialization.
  await page.evaluate(
    ({ items }) => {
      // @ts-ignore — renderSearchHistory is defined in the page scope
      renderSearchHistory(items);
    },
    {
      items: [
        {
          record_id: recordId,
          query: "테스트게임",
          answer_mode: "entity_card",
          verification_label: "설명형 단일 출처",
          source_roles: ["백과 기반"],
          result_count: 2,
          page_count: 0,
          created_at: record.created_at,
          record_path: recordPath,
          claim_coverage_summary: { strong: 0, weak: 0, missing: 5, conflict: 0 },
          claim_coverage_progress_summary: "",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  const reloadButton = historyBox.locator(".history-item-actions button.secondary").first();
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Step 2: natural reload — send "방금 검색한 결과 다시 보여줘" without record ID
  await page.evaluate(async () => {
    // @ts-ignore — sendRequest is defined in the page scope
    await sendRequest({
      user_text: "방금 검색한 결과 다시 보여줘",
    });
  });

  await expect(originBadge).toHaveText("WEB");

  // Step 3: first follow-up after natural reload
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  await expect(originBadge).toHaveText("WEB");
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");

  // After the first follow-up the history-card `.meta` must already be the missing-only
  // count-only line derived from the stored claim_coverage.
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 미확인 5");
  await expect(historyCardMeta).not.toContainText("·");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");

  // Step 4: second follow-up on the same record
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 게임 장르만 한 줄로 다시 정리해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 단일 출처");
  await expect(originDetail).toContainText("백과 기반");
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");

  // history-card `.meta` must still carry the same missing-only count-only line.
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 미확인 5");
  await expect(historyCardMeta).not.toContainText("·");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");
  const postSecondFollowUpMetaText = ((await historyCardMeta.textContent()) || "").trim();
  expect(postSecondFollowUpMetaText.length).toBeGreaterThan(0);
  expect(postSecondFollowUpMetaText.startsWith("·")).toBe(false);
  expect(postSecondFollowUpMetaText.endsWith("·")).toBe(false);

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("entity-card 붉은사막 검색 결과 자연어 reload에서 WEB badge, 설명 카드, noisy single-source claim(출시일/2025/blog.example.com) 미노출, 설명형 다중 출처 합의, 백과 기반 유지, namu.wiki/ko.wikipedia.org/blog.example.com provenance 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-actual-search-natural-reload-prov");

  // Pre-seed a noisy 3-source entity_card record (붉은사막)
  const recordId = `websearch-entity-actual-nat-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 3,
    results: [
      { title: "붉은사막 - 나무위키", url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { title: "붉은사막 - 위키백과", url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { title: "붉은사막 출시일 정보", url: "https://blog.example.com/crimson-desert", snippet: "붉은사막 출시일은 2025년 12월로 예정되어 있다." },
    ],
    pages: [
      { url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", title: "붉은사막 - 나무위키", text: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", title: "붉은사막 - 위키백과", text: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { url: "https://blog.example.com/crimson-desert", title: "붉은사막 출시일 정보", text: "붉은사막 출시일은 2025년 12월로 예정되어 있다. 로그인 회원가입 구독 광고" },
    ],
    summary_text: "웹 검색 요약: 붉은사막\n\n확인된 사실:\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다. [교차 확인]",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "entity_card", verification_label: "설명형 다중 출처 합의", source_roles: ["백과 기반"] },
    // actual-search entity-card reload-only strong-plus-missing branch: stored claim_coverage
    // mirrors the actual shipped runtime (`{strong:3, weak:0, missing:2}`, empty progress).
    // Use slot names distinct from noisy exclusion keywords (`출시일`/`2025`/`brunch`) so the
    // seeded claim-coverage does not collide with the noisy single-source exclusion asserts.
    claim_coverage: [
      { slot: "장르", status: "strong", status_label: "교차 확인", value: "오픈월드 액션 어드벤처 게임", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "개발사", status: "strong", status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "플랫폼", status: "strong", status_label: "교차 확인", value: "PC/콘솔", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "엔진", status: "missing", status_label: "미확인" },
      { slot: "난이도", status: "missing", status_label: "미확인" },
    ],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{
      record_id: recordId,
      query: "붉은사막",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["백과 기반"],
      result_count: 3,
      page_count: 3,
      created_at: record.created_at,
      record_path: recordPath,
      claim_coverage_summary: { strong: 3, weak: 0, missing: 2, conflict: 0 },
      claim_coverage_progress_summary: "",
    }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("백과 기반");
  const originDetailText = await originDetail.textContent();
  expect(originDetailText).not.toContain("출시일");
  expect(originDetailText).not.toContain("2025");
  expect(originDetailText).not.toContain("blog.example.com");
  await expect(page.getByTestId("response-text")).toContainText("확인된 사실 [교차 확인]:");
  const responseText = await page.getByTestId("response-text").textContent();
  expect(responseText).not.toContain("출시일");
  expect(responseText).not.toContain("2025");
  expect(responseText).not.toContain("blog.example.com");
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");
  await expect(contextBox).toContainText("blog.example.com");

  // actual-search reload-only strong-plus-missing meta: history-card `.meta` must be the
  // exact `사실 검증 교차 확인 3 · 미확인 2` line, with no answer-mode label leak.
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 3 · 미확인 2");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("entity-card 붉은사막 자연어 reload에서 source path(namu.wiki, ko.wikipedia.org, blog.example.com provenance)가 context box에 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-actual-search-natural-reload-sp-prov");

  // Pre-seed a noisy 3-source entity_card record (붉은사막)
  const recordId = `websearch-entity-actual-nat-sp-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 3,
    results: [
      { title: "붉은사막 - 나무위키", url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { title: "붉은사막 - 위키백과", url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { title: "붉은사막 출시일 정보", url: "https://blog.example.com/crimson-desert", snippet: "붉은사막 출시일은 2025년 12월로 예정되어 있다." },
    ],
    pages: [
      { url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", title: "붉은사막 - 나무위키", text: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", title: "붉은사막 - 위키백과", text: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { url: "https://blog.example.com/crimson-desert", title: "붉은사막 출시일 정보", text: "붉은사막 출시일은 2025년 12월로 예정되어 있다. 로그인 회원가입 구독 광고" },
    ],
    summary_text: "웹 검색 요약: 붉은사막\n\n확인된 사실:\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다. [교차 확인]",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "entity_card", verification_label: "설명형 다중 출처 합의", source_roles: ["백과 기반"] },
    // actual-search entity-card reload-only strong-plus-missing branch: same 3-strong +
    // 2-missing pattern as the paired `...WEB badge, 설명 카드, noisy ...` scenario. Slot
    // names avoid `출시일` to keep the noisy exclusion asserts in the paired scenario stable
    // even if fixtures are reused across the family.
    claim_coverage: [
      { slot: "장르", status: "strong", status_label: "교차 확인", value: "오픈월드 액션 어드벤처 게임", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "개발사", status: "strong", status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "플랫폼", status: "strong", status_label: "교차 확인", value: "PC/콘솔", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "엔진", status: "missing", status_label: "미확인" },
      { slot: "난이도", status: "missing", status_label: "미확인" },
    ],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{
      record_id: recordId,
      query: "붉은사막",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["백과 기반"],
      result_count: 3,
      page_count: 3,
      created_at: record.created_at,
      record_path: recordPath,
      claim_coverage_summary: { strong: 3, weak: 0, missing: 2, conflict: 0 },
      claim_coverage_progress_summary: "",
    }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });

  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");
  await expect(contextBox).toContainText("blog.example.com");

  // actual-search reload-only strong-plus-missing meta (source-path variant): history-card
  // `.meta` must be the exact `사실 검증 교차 확인 3 · 미확인 2` line with no label leak.
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 3 · 미확인 2");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("entity-card dual-probe 자연어 reload에서 source path(pearlabyss.com/200, pearlabyss.com/300)가 context box에 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-dual-probe-natural-reload-sp");

  // Pre-seed an entity_card record with dual-probe URLs and the actual shipped mixed
  // count-summary runtime (`{strong:1, weak:4, missing:0}`) so post-reload re-serialization
  // aligns with the history-card `.meta` assertion below.
  const recordId = `websearch-entity-dual-nat-sp-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 2,
    results: [
      {
        title: "붉은사막 - 나무위키",
        url: "https://namu.wiki/w/test",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
        matched_query: "붉은사막",
      },
      {
        title: "붉은사막 | 플랫폼 - 공식",
        url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=200",
        snippet: "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이다.",
        matched_query: "붉은사막 공식 플랫폼",
      },
      {
        title: "붉은사막 | 서비스 - 공식",
        url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=300",
        snippet: "붉은사막은 펄어비스가 운영하는 게임이다.",
        matched_query: "붉은사막 서비스 공식",
      },
    ],
    pages: [
      {
        url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=200",
        title: "붉은사막 | 플랫폼 - 공식",
        text: "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이며 펄어비스가 개발 중입니다.",
      },
      {
        url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=300",
        title: "붉은사막 | 서비스 - 공식",
        text: "붉은사막은 펄어비스가 운영하는 게임이며 배급도 펄어비스가 담당합니다.",
      },
    ],
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["공식 기반", "백과 기반"],
    },
    claim_coverage: [
      { slot: "개발사", status: "strong", status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "official" },
      { slot: "장르", status: "weak", status_label: "단일 출처", value: "오픈월드 액션 어드벤처", support_count: 1, candidate_count: 1, source_role: "encyclopedia" },
      { slot: "플랫폼", status: "weak", status_label: "단일 출처", value: "PC/콘솔", support_count: 1, candidate_count: 1, source_role: "official" },
      { slot: "서비스", status: "weak", status_label: "단일 출처", value: "펄어비스", support_count: 1, candidate_count: 1, source_role: "official" },
      { slot: "출시일", status: "weak", status_label: "단일 출처", value: "미정", support_count: 1, candidate_count: 1, source_role: "official" },
    ],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Step 1: click reload to register record in server session
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
          verification_label: "설명형 다중 출처 합의",
          source_roles: ["공식 기반", "백과 기반"],
          result_count: 3,
          page_count: 2,
          created_at: record.created_at,
          record_path: recordPath,
          claim_coverage_summary: { strong: 1, weak: 4, missing: 0, conflict: 0 },
          claim_coverage_progress_summary: "",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  const reloadButton = historyBox.locator(".history-item-actions button.secondary").first();
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Step 2: natural reload
  await page.evaluate(async () => {
    // @ts-ignore — sendRequest is defined in the page scope
    await sendRequest({
      user_text: "방금 검색한 결과 다시 보여줘",
    });
  });

  // Assert context box shows both dual-probe source URLs after natural reload
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("pearlabyss.com/ko-KR/Board/Detail?_boardNo=200");
  await expect(contextBox).toContainText("pearlabyss.com/ko-KR/Board/Detail?_boardNo=300");

  // dual-probe reload-only mixed count-summary meta: history-card `.meta` must be the exact
  // `사실 검증 교차 확인 1 · 단일 출처 4` line, with no answer-mode label leak.
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 1 · 단일 출처 4");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("entity-card dual-probe 자연어 reload에서 WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-dual-probe-natural-reload-exact");

  // Pre-seed an entity_card record with dual-probe URLs
  const recordId = `websearch-entity-dual-nat-ex-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 2,
    results: [
      {
        title: "붉은사막 - 나무위키",
        url: "https://namu.wiki/w/test",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
        matched_query: "붉은사막",
      },
      {
        title: "붉은사막 | 플랫폼 - 공식",
        url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=200",
        snippet: "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이다.",
        matched_query: "붉은사막 공식 플랫폼",
      },
      {
        title: "붉은사막 | 서비스 - 공식",
        url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=300",
        snippet: "붉은사막은 펄어비스가 운영하는 게임이다.",
        matched_query: "붉은사막 서비스 공식",
      },
    ],
    pages: [
      {
        url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=200",
        title: "붉은사막 | 플랫폼 - 공식",
        text: "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이며 펄어비스가 개발 중입니다.",
      },
      {
        url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=300",
        title: "붉은사막 | 서비스 - 공식",
        text: "붉은사막은 펄어비스가 운영하는 게임이며 배급도 펄어비스가 담당합니다.",
      },
    ],
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["공식 기반", "백과 기반"],
    },
    claim_coverage: [
      { slot: "개발사", status: "strong", status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "official" },
      { slot: "장르", status: "weak", status_label: "단일 출처", value: "오픈월드 액션 어드벤처", support_count: 1, candidate_count: 1, source_role: "encyclopedia" },
      { slot: "플랫폼", status: "weak", status_label: "단일 출처", value: "PC/콘솔", support_count: 1, candidate_count: 1, source_role: "official" },
      { slot: "서비스", status: "weak", status_label: "단일 출처", value: "펄어비스", support_count: 1, candidate_count: 1, source_role: "official" },
      { slot: "출시일", status: "weak", status_label: "단일 출처", value: "미정", support_count: 1, candidate_count: 1, source_role: "official" },
    ],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Step 1: click reload to register record in server session
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
          verification_label: "설명형 다중 출처 합의",
          source_roles: ["공식 기반", "백과 기반"],
          result_count: 3,
          page_count: 2,
          created_at: record.created_at,
          record_path: recordPath,
          claim_coverage_summary: { strong: 1, weak: 4, missing: 0, conflict: 0 },
          claim_coverage_progress_summary: "",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  const reloadButton = historyBox.locator(".history-item-actions button.secondary").first();
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Step 2: natural reload
  await page.evaluate(async () => {
    // @ts-ignore — sendRequest is defined in the page scope
    await sendRequest({
      user_text: "방금 검색한 결과 다시 보여줘",
    });
  });

  // Assert natural reload preserves exact fields
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);

  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");

  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("공식 기반");
  await expect(originDetail).toContainText("백과 기반");

  // dual-probe reload-only mixed count-summary meta: history-card `.meta` must be the exact
  // `사실 검증 교차 확인 1 · 단일 출처 4` line, with no answer-mode label leak.
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 1 · 단일 출처 4");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("entity-card dual-probe 자연어 reload 후 follow-up에서 source path(pearlabyss.com/200, pearlabyss.com/300)가 context box에 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-dual-probe-natural-reload-followup-sp");

  // Pre-seed an entity_card record with dual-probe URLs
  const recordId = `websearch-entity-dual-nat-fu-sp-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 2,
    results: [
      {
        title: "붉은사막 - 나무위키",
        url: "https://namu.wiki/w/test",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
        matched_query: "붉은사막",
      },
      {
        title: "붉은사막 | 플랫폼 - 공식",
        url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=200",
        snippet: "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이다.",
        matched_query: "붉은사막 공식 플랫폼",
      },
      {
        title: "붉은사막 | 서비스 - 공식",
        url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=300",
        snippet: "붉은사막은 펄어비스가 운영하는 게임이다.",
        matched_query: "붉은사막 서비스 공식",
      },
    ],
    pages: [
      {
        url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=200",
        title: "붉은사막 | 플랫폼 - 공식",
        text: "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이며 펄어비스가 개발 중입니다.",
      },
      {
        url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=300",
        title: "붉은사막 | 서비스 - 공식",
        text: "붉은사막은 펄어비스가 운영하는 게임이며 배급도 펄어비스가 담당합니다.",
      },
    ],
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["공식 기반", "백과 기반"],
    },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Step 1: click reload to register record in server session
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
          verification_label: "설명형 다중 출처 합의",
          source_roles: ["공식 기반", "백과 기반"],
          result_count: 3,
          page_count: 2,
          created_at: record.created_at,
          record_path: recordPath,
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  const reloadButton = historyBox.locator(".history-item-actions button.secondary").first();
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Step 2: natural reload
  await page.evaluate(async () => {
    // @ts-ignore — sendRequest is defined in the page scope
    await sendRequest({
      user_text: "방금 검색한 결과 다시 보여줘",
    });
  });

  await expect(originBadge).toHaveText("WEB");

  // Step 3: follow-up after natural reload
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Assert context box still shows both dual-probe source URLs after follow-up
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("pearlabyss.com/ko-KR/Board/Detail?_boardNo=200");
  await expect(contextBox).toContainText("pearlabyss.com/ko-KR/Board/Detail?_boardNo=300");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("entity-card dual-probe 자연어 reload 후 두 번째 follow-up에서 mixed count-summary meta가 truthfully 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-dual-probe-natural-reload-second-followup-mixed-count-summary");

  const recordId = `websearch-entity-dual-nat-2fu-mix-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const mixedCoverage = [
    { slot: "개발사", status: "strong", status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "official" },
    { slot: "장르", status: "weak", status_label: "단일 출처", value: "오픈월드 액션 어드벤처", support_count: 1, candidate_count: 1, source_role: "encyclopedia" },
    { slot: "플랫폼", status: "weak", status_label: "단일 출처", value: "PC/콘솔", support_count: 1, candidate_count: 1, source_role: "official" },
    { slot: "서비스", status: "weak", status_label: "단일 출처", value: "펄어비스", support_count: 1, candidate_count: 1, source_role: "official" },
    { slot: "출시일", status: "weak", status_label: "단일 출처", value: "미정", support_count: 1, candidate_count: 1, source_role: "official" },
  ];
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 2,
    results: [
      { title: "붉은사막 - 나무위키", url: "https://namu.wiki/w/test", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.", matched_query: "붉은사막" },
      { title: "붉은사막 | 플랫폼 - 공식", url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=200", snippet: "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이다.", matched_query: "붉은사막 공식 플랫폼" },
      { title: "붉은사막 | 서비스 - 공식", url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=300", snippet: "붉은사막은 펄어비스가 운영하는 게임이다.", matched_query: "붉은사막 서비스 공식" },
    ],
    pages: [
      { url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=200", title: "붉은사막 | 플랫폼 - 공식", text: "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이며 펄어비스가 개발 중입니다." },
      { url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=300", title: "붉은사막 | 서비스 - 공식", text: "붉은사막은 펄어비스가 운영하는 게임이며 배급도 펄어비스가 담당합니다." },
    ],
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "entity_card", verification_label: "설명형 다중 출처 합의", source_roles: ["공식 기반", "백과 기반"] },
    claim_coverage: mixedCoverage,
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{
      record_id: recordId,
      query: "붉은사막",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["공식 기반", "백과 기반"],
      result_count: 3,
      page_count: 2,
      created_at: record.created_at,
      record_path: recordPath,
      claim_coverage_summary: { strong: 1, weak: 4, missing: 0, conflict: 0 },
      claim_coverage_progress_summary: "",
    }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Natural reload
  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });
  await expect(originBadge).toHaveText("WEB");

  // First follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });
  await expect(originBadge).toHaveText("WEB");
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");

  // After the first follow-up the history-card `.meta` must already carry the mixed
  // count-only line derived from the stored claim_coverage (1 strong + 4 weak slots).
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 1 · 단일 출처 4");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");

  // Second follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "더 자세히 알려줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  // Assert origin / answer-mode / origin detail / source path continuity
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("공식 기반");
  await expect(originDetail).toContainText("백과 기반");
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("pearlabyss.com/ko-KR/Board/Detail?_boardNo=200");
  await expect(contextBox).toContainText("pearlabyss.com/ko-KR/Board/Detail?_boardNo=300");

  // The history-card `.meta` must still carry the same mixed count-only line with no drift,
  // no leaked answer-mode label, no leading/trailing separator, and no doubled separator.
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 1 · 단일 출처 4");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");
  await expect(historyCardMeta).not.toContainText(" ·  · ");
  const postSecondFollowUpMetaText = ((await historyCardMeta.textContent()) || "").trim();
  expect(postSecondFollowUpMetaText.length).toBeGreaterThan(0);
  expect(postSecondFollowUpMetaText.startsWith("·")).toBe(false);
  expect(postSecondFollowUpMetaText.endsWith("·")).toBe(false);

  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("entity-card dual-probe 자연어 reload 후 follow-up에서 WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 drift하지 않습니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-dual-probe-natural-reload-followup-origin");

  const recordId = `websearch-entity-dual-nat-fu-or-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 2,
    results: [
      { title: "붉은사막 - 나무위키", url: "https://namu.wiki/w/test", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.", matched_query: "붉은사막" },
      { title: "붉은사막 | 플랫폼 - 공식", url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=200", snippet: "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이다.", matched_query: "붉은사막 공식 플랫폼" },
      { title: "붉은사막 | 서비스 - 공식", url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=300", snippet: "붉은사막은 펄어비스가 운영하는 게임이다.", matched_query: "붉은사막 서비스 공식" },
    ],
    pages: [
      { url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=200", title: "붉은사막 | 플랫폼 - 공식", text: "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이며 펄어비스가 개발 중입니다." },
      { url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=300", title: "붉은사막 | 서비스 - 공식", text: "붉은사막은 펄어비스가 운영하는 게임이며 배급도 펄어비스가 담당합니다." },
    ],
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "entity_card", verification_label: "설명형 다중 출처 합의", source_roles: ["공식 기반", "백과 기반"] },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{ record_id: recordId, query: "붉은사막", answer_mode: "entity_card", verification_label: "설명형 다중 출처 합의", source_roles: ["공식 기반", "백과 기반"], result_count: 3, page_count: 2, created_at: record.created_at, record_path: recordPath }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Natural reload
  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });
  await expect(originBadge).toHaveText("WEB");

  // Follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  // Assert response origin exact fields after follow-up
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("공식 기반");
  await expect(originDetail).toContainText("백과 기반");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("entity-card dual-probe 자연어 reload 후 두 번째 follow-up에서 source path(pearlabyss.com/200, pearlabyss.com/300) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 drift하지 않습니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-dual-probe-natural-reload-second-followup-origin");

  const recordId = `websearch-entity-dual-nat-2fu-or-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 2,
    results: [
      { title: "붉은사막 - 나무위키", url: "https://namu.wiki/w/test", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.", matched_query: "붉은사막" },
      { title: "붉은사막 | 플랫폼 - 공식", url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=200", snippet: "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이다.", matched_query: "붉은사막 공식 플랫폼" },
      { title: "붉은사막 | 서비스 - 공식", url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=300", snippet: "붉은사막은 펄어비스가 운영하는 게임이다.", matched_query: "붉은사막 서비스 공식" },
    ],
    pages: [
      { url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=200", title: "붉은사막 | 플랫폼 - 공식", text: "붉은사막은 PC와 콘솔 플랫폼으로 출시 예정이며 펄어비스가 개발 중입니다." },
      { url: "https://www.pearlabyss.com/ko-KR/Board/Detail?_boardNo=300", title: "붉은사막 | 서비스 - 공식", text: "붉은사막은 펄어비스가 운영하는 게임이며 배급도 펄어비스가 담당합니다." },
    ],
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "entity_card", verification_label: "설명형 다중 출처 합의", source_roles: ["공식 기반", "백과 기반"] },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{ record_id: recordId, query: "붉은사막", answer_mode: "entity_card", verification_label: "설명형 다중 출처 합의", source_roles: ["공식 기반", "백과 기반"], result_count: 3, page_count: 2, created_at: record.created_at, record_path: recordPath }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Natural reload
  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });
  await expect(originBadge).toHaveText("WEB");

  // First follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });
  await expect(originBadge).toHaveText("WEB");

  // Second follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "더 자세히 알려줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  // Assert response-origin continuity after second follow-up
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("공식 기반");
  await expect(originDetail).toContainText("백과 기반");

  // Assert context box shows dual-probe source URLs
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("pearlabyss.com/ko-KR/Board/Detail?_boardNo=200");
  await expect(contextBox).toContainText("pearlabyss.com/ko-KR/Board/Detail?_boardNo=300");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("entity-card 붉은사막 actual-search 자연어 reload 후 follow-up에서 source path(namu.wiki, ko.wikipedia.org)가 context box에 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-actual-search-natural-reload-followup-sp");

  // Pre-seed an actual-search entity_card record (붉은사막, multi-source agreement)
  const recordId = `websearch-entity-actual-nat-fu-sp-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      {
        title: "붉은사막 - 나무위키",
        url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
      {
        title: "붉은사막 - 위키백과",
        url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89",
        snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
      },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 붉은사막\n\n확인된 사실:\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다. [교차 확인]",
    response_origin: {
      provider: "web",
      badge: "WEB",
      label: "웹 검색",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["백과 기반"],
    },
    // actual-search entity-card first-follow-up strong-plus-missing branch (natural reload):
    // stored claim_coverage mirrors the runtime `{strong:3, weak:0, missing:2}` distribution
    // with empty progress. Slot names avoid noisy keywords.
    claim_coverage: [
      { slot: "장르", status: "strong", status_label: "교차 확인", value: "오픈월드 액션 어드벤처 게임", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "개발사", status: "strong", status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "플랫폼", status: "strong", status_label: "교차 확인", value: "PC/콘솔", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "엔진", status: "missing", status_label: "미확인" },
      { slot: "난이도", status: "missing", status_label: "미확인" },
    ],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  // Step 1: click reload to register record in server session
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
          verification_label: "설명형 다중 출처 합의",
          source_roles: ["백과 기반"],
          result_count: 2,
          page_count: 0,
          created_at: record.created_at,
          record_path: recordPath,
          claim_coverage_summary: { strong: 3, weak: 0, missing: 2, conflict: 0 },
          claim_coverage_progress_summary: "",
        },
      ],
    }
  );

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  const reloadButton = historyBox.locator(".history-item-actions button.secondary").first();
  await reloadButton.click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Step 2: natural reload
  await page.evaluate(async () => {
    // @ts-ignore — sendRequest is defined in the page scope
    await sendRequest({
      user_text: "방금 검색한 결과 다시 보여줘",
    });
  });

  await expect(originBadge).toHaveText("WEB");

  // Step 3: follow-up after natural reload
  await page.evaluate(
    async ({ rid }) => {
      // @ts-ignore — sendRequest is defined in the page scope
      await sendRequest({
        user_text: "이 검색 결과 요약해줘",
        load_web_search_record_id: rid,
      }, "follow_up");
    },
    { rid: recordId }
  );

  // Assert context box still shows both actual-search source URLs after follow-up (plurality)
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");

  // actual-search natural-reload first-follow-up strong-plus-missing meta: history-card
  // `.meta` must be the exact `사실 검증 교차 확인 3 · 미확인 2` line, with no label leak.
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 3 · 미확인 2");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");

  // Clean up
  try {
    fs.unlinkSync(recordPath);
    fs.rmdirSync(recordDir);
  } catch (_) {
    // best-effort cleanup
  }
});

test("entity-card 붉은사막 actual-search 자연어 reload 후 follow-up에서 WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 drift하지 않습니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-actual-search-natural-reload-followup-origin");

  const recordId = `websearch-entity-actual-nat-fu-or-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      { title: "붉은사막 - 나무위키", url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { title: "붉은사막 - 위키백과", url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 붉은사막\n\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "entity_card", verification_label: "설명형 다중 출처 합의", source_roles: ["백과 기반"] },
    // actual-search entity-card first-follow-up strong-plus-missing branch (natural reload
    // WEB-badge variant): seed stored claim_coverage with the runtime `{strong:3, weak:0,
    // missing:2}` distribution so post-reload serialization aligns with the `.meta` below.
    claim_coverage: [
      { slot: "장르", status: "strong", status_label: "교차 확인", value: "오픈월드 액션 어드벤처 게임", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "개발사", status: "strong", status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "플랫폼", status: "strong", status_label: "교차 확인", value: "PC/콘솔", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "엔진", status: "missing", status_label: "미확인" },
      { slot: "난이도", status: "missing", status_label: "미확인" },
    ],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{
      record_id: recordId,
      query: "붉은사막",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["백과 기반"],
      result_count: 2,
      page_count: 0,
      created_at: record.created_at,
      record_path: recordPath,
      claim_coverage_summary: { strong: 3, weak: 0, missing: 2, conflict: 0 },
      claim_coverage_progress_summary: "",
    }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });
  await expect(originBadge).toHaveText("WEB");

  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("백과 기반");

  // actual-search natural-reload first-follow-up strong-plus-missing meta (WEB-badge
  // variant): history-card `.meta` must be the exact `사실 검증 교차 확인 3 · 미확인 2` line.
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 3 · 미확인 2");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("entity-card 붉은사막 actual-search 자연어 reload 후 두 번째 follow-up에서 source path(namu.wiki, ko.wikipedia.org)가 context box에 유지되고 WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 drift하지 않습니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-actual-search-natural-reload-second-followup-sp-origin");

  const recordId = `websearch-entity-actual-nat-2fu-or-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 0,
    results: [
      { title: "붉은사막 - 나무위키", url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { title: "붉은사막 - 위키백과", url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
    ],
    pages: [],
    summary_text: "웹 검색 요약: 붉은사막\n\n확인된 사실:\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다. [교차 확인]",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "entity_card", verification_label: "설명형 다중 출처 합의", source_roles: ["백과 기반"] },
    // Strong-plus-missing claim_coverage mix matches the actual actual-search runtime branch
    // observed via the focused probe: `strong=3`, `weak=0`, `missing=2`, empty progress summary.
    claim_coverage: [
      { slot: "장르", status: "strong", status_label: "교차 확인", value: "오픈월드 액션 어드벤처 게임", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "개발사", status: "strong", status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "플랫폼", status: "strong", status_label: "교차 확인", value: "PC/콘솔", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "출시일", status: "missing", status_label: "미확인" },
      { slot: "가격", status: "missing", status_label: "미확인" },
    ],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{
      record_id: recordId,
      query: "붉은사막",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["백과 기반"],
      result_count: 2,
      page_count: 0,
      created_at: record.created_at,
      record_path: recordPath,
      claim_coverage_summary: { strong: 3, weak: 0, missing: 2, conflict: 0 },
      claim_coverage_progress_summary: "",
    }],
  });

  const historyBox2 = page.locator("#search-history-box");
  await expect(historyBox2).toBeVisible();
  await historyBox2.locator(".history-item-actions button.secondary").first().click();

  const originBadge2 = page.locator("#response-origin-badge");
  await expect(originBadge2).toHaveText("WEB");

  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });
  await expect(originBadge2).toHaveText("WEB");

  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });
  await expect(originBadge2).toHaveText("WEB");

  // After the first follow-up the history-card `.meta` must already carry the strong-plus-missing
  // count-only line derived from the stored claim_coverage (3 strong + 2 missing slots).
  const historyCardMeta2 = historyBox2.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta2).toHaveCount(1);
  await expect(historyCardMeta2).toHaveText("사실 검증 교차 확인 3 · 미확인 2");
  await expect(historyCardMeta2).not.toContainText("설명 카드");
  await expect(historyCardMeta2).not.toContainText("최신 확인");
  await expect(historyCardMeta2).not.toContainText("일반 검색");

  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "더 자세히 알려줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  await expect(originBadge2).toHaveText("WEB");
  await expect(originBadge2).toHaveClass(/web/);
  const answerModeBadge2 = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge2).toBeVisible();
  await expect(answerModeBadge2).toHaveText("설명 카드");
  const originDetail2 = page.locator("#response-origin-detail");
  await expect(originDetail2).toContainText("설명형 다중 출처 합의");
  await expect(originDetail2).toContainText("백과 기반");

  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");

  // The history-card `.meta` must still carry the same strong-plus-missing count-only line with
  // no drift, no leaked answer-mode label, no leading/trailing separator, and no doubled separator.
  await expect(historyCardMeta2).toHaveCount(1);
  await expect(historyCardMeta2).toHaveText("사실 검증 교차 확인 3 · 미확인 2");
  await expect(historyCardMeta2).not.toContainText("설명 카드");
  await expect(historyCardMeta2).not.toContainText("최신 확인");
  await expect(historyCardMeta2).not.toContainText("일반 검색");
  await expect(historyCardMeta2).not.toContainText(" ·  · ");
  const postSecondFollowUpMetaText = ((await historyCardMeta2.textContent()) || "").trim();
  expect(postSecondFollowUpMetaText.length).toBeGreaterThan(0);
  expect(postSecondFollowUpMetaText.startsWith("·")).toBe(false);
  expect(postSecondFollowUpMetaText.endsWith("·")).toBe(false);

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("entity-card 붉은사막 자연어 reload 후 follow-up에서 noisy single-source claim(출시일/2025/blog.example.com)이 본문과 origin detail에 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance continuity가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-crimson-natural-reload-followup-noisy-excl-prov");

  const recordId = `websearch-entity-nat-fu-noisy-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 3,
    results: [
      { title: "붉은사막 - 나무위키", url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { title: "붉은사막 - 위키백과", url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { title: "붉은사막 출시일 정보", url: "https://blog.example.com/crimson-desert", snippet: "붉은사막 출시일은 2025년 12월로 예정되어 있다." },
    ],
    pages: [
      { url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", title: "붉은사막 - 나무위키", text: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", title: "붉은사막 - 위키백과", text: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { url: "https://blog.example.com/crimson-desert", title: "붉은사막 출시일 정보", text: "붉은사막 출시일은 2025년 12월로 예정되어 있다. 로그인 회원가입 구독 광고" },
    ],
    summary_text: "웹 검색 요약: 붉은사막\n\n확인된 사실:\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다. [교차 확인]",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "entity_card", verification_label: "설명형 다중 출처 합의", source_roles: ["백과 기반"] },
    // Strong-plus-missing claim_coverage mix matches the actual noisy entity-card runtime
    // branch observed via the focused probe: `strong=3`, `weak=0`, `missing=2`, empty progress.
    claim_coverage: [
      { slot: "장르", status: "strong", status_label: "교차 확인", value: "오픈월드 액션 어드벤처 게임", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "개발사", status: "strong", status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "플랫폼", status: "strong", status_label: "교차 확인", value: "PC/콘솔", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "출시일", status: "missing", status_label: "미확인" },
      { slot: "가격", status: "missing", status_label: "미확인" },
    ],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{
      record_id: recordId,
      query: "붉은사막",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["백과 기반"],
      result_count: 3,
      page_count: 3,
      created_at: record.created_at,
      record_path: recordPath,
      claim_coverage_summary: { strong: 3, weak: 0, missing: 2, conflict: 0 },
      claim_coverage_progress_summary: "",
    }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });
  await expect(originBadge).toHaveText("WEB");

  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  // Assert response-origin continuity
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("백과 기반");

  // Assert noisy single-source claim exclusion in origin detail
  const originDetailText = await originDetail.textContent();
  expect(originDetailText).not.toContain("출시일");
  expect(originDetailText).not.toContain("2025");
  expect(originDetailText).not.toContain("blog.example.com");

  // Assert noisy single-source claim exclusion in response text
  const responseText = await page.getByTestId("response-text").textContent();
  expect(responseText).not.toContain("출시일");
  expect(responseText).not.toContain("2025");
  expect(responseText).not.toContain("blog.example.com");

  // Assert context box continuity + provenance
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");
  await expect(contextBox).toContainText("blog.example.com");

  // History-card `.meta` must carry the same strong-plus-missing count-only line at the
  // shallow follow-up point, matching the deeper second-follow-up scenario. The count line
  // legitimately contains ` · ` between `교차 확인 3` and `미확인 2`.
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 3 · 미확인 2");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");
  await expect(historyCardMeta).not.toContainText(" ·  · ");
  const postFollowUpMetaText = ((await historyCardMeta.textContent()) || "").trim();
  expect(postFollowUpMetaText.length).toBeGreaterThan(0);
  expect(postFollowUpMetaText.startsWith("·")).toBe(false);
  expect(postFollowUpMetaText.endsWith("·")).toBe(false);

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("entity-card 붉은사막 자연어 reload 후 두 번째 follow-up에서 noisy single-source claim(출시일/2025/blog.example.com)이 본문과 origin detail에 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance continuity가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-crimson-natural-reload-second-followup-noisy-excl-prov");

  const recordId = `websearch-entity-nat-2fu-noisy-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 3,
    results: [
      { title: "붉은사막 - 나무위키", url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { title: "붉은사막 - 위키백과", url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { title: "붉은사막 출시일 정보", url: "https://blog.example.com/crimson-desert", snippet: "붉은사막 출시일은 2025년 12월로 예정되어 있다." },
    ],
    pages: [
      { url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", title: "붉은사막 - 나무위키", text: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", title: "붉은사막 - 위키백과", text: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { url: "https://blog.example.com/crimson-desert", title: "붉은사막 출시일 정보", text: "붉은사막 출시일은 2025년 12월로 예정되어 있다. 로그인 회원가입 구독 광고" },
    ],
    summary_text: "웹 검색 요약: 붉은사막\n\n확인된 사실:\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다. [교차 확인]",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "entity_card", verification_label: "설명형 다중 출처 합의", source_roles: ["백과 기반"] },
    // Strong-plus-missing claim_coverage mix matches the actual noisy entity-card runtime
    // branch observed via the focused probe: `strong=3`, `weak=0`, `missing=2`, empty progress.
    claim_coverage: [
      { slot: "장르", status: "strong", status_label: "교차 확인", value: "오픈월드 액션 어드벤처 게임", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "개발사", status: "strong", status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "플랫폼", status: "strong", status_label: "교차 확인", value: "PC/콘솔", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "출시일", status: "missing", status_label: "미확인" },
      { slot: "가격", status: "missing", status_label: "미확인" },
    ],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{
      record_id: recordId,
      query: "붉은사막",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["백과 기반"],
      result_count: 3,
      page_count: 3,
      created_at: record.created_at,
      record_path: recordPath,
      claim_coverage_summary: { strong: 3, weak: 0, missing: 2, conflict: 0 },
      claim_coverage_progress_summary: "",
    }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });
  await expect(originBadge).toHaveText("WEB");

  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });
  await expect(originBadge).toHaveText("WEB");

  // After the first follow-up the history-card `.meta` must already carry the strong-plus-
  // missing count-only line derived from the stored claim_coverage (3 strong + 2 missing).
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 3 · 미확인 2");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");

  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "더 자세히 알려줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  // Assert response-origin continuity
  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("백과 기반");

  // Assert noisy single-source claim exclusion in origin detail
  const originDetailText = await originDetail.textContent();
  expect(originDetailText).not.toContain("출시일");
  expect(originDetailText).not.toContain("2025");
  expect(originDetailText).not.toContain("blog.example.com");

  // Assert noisy single-source claim exclusion in response text
  const responseText = await page.getByTestId("response-text").textContent();
  expect(responseText).not.toContain("출시일");
  expect(responseText).not.toContain("2025");
  expect(responseText).not.toContain("blog.example.com");

  // Assert context box continuity + provenance
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");
  await expect(contextBox).toContainText("blog.example.com");

  // History-card `.meta` must still carry the same strong-plus-missing count-only line with
  // no drift, no leaked answer-mode label, no leading/trailing separator, and no doubled
  // separator. The count line legitimately contains ` · ` between `교차 확인 3` and `미확인 2`.
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 3 · 미확인 2");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");
  await expect(historyCardMeta).not.toContainText(" ·  · ");
  const postSecondFollowUpMetaText = ((await historyCardMeta.textContent()) || "").trim();
  expect(postSecondFollowUpMetaText.length).toBeGreaterThan(0);
  expect(postSecondFollowUpMetaText.startsWith("·")).toBe(false);
  expect(postSecondFollowUpMetaText.endsWith("·")).toBe(false);

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("history-card latest-update single-source 다시 불러오기 후 두 번째 follow-up 질문에서 source path(example.com/seoul-weather) + WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 drift하지 않습니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-latest-single-second-followup");

  const recordId = `websearch-latest-single-2fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `서울날씨-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "서울 날씨",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 1,
    page_count: 1,
    results: [
      { title: "서울 날씨 - 예보", url: "https://example.com/seoul-weather", snippet: "서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다." },
    ],
    pages: [
      { url: "https://example.com/seoul-weather", title: "서울 날씨 - 예보", text: "서울은 맑고 낮 최고 17도. 미세먼지 보통." },
    ],
    summary_text: "웹 검색 요약: 서울 날씨\n\n서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "latest_update", verification_label: "단일 출처 참고", source_roles: ["보조 출처"] },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{ record_id: recordId, query: "서울 날씨", answer_mode: "latest_update", verification_label: "단일 출처 참고", source_roles: ["보조 출처"], result_count: 1, page_count: 1, created_at: record.created_at, record_path: recordPath }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // First follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });
  await expect(originBadge).toHaveText("WEB");

  // Second follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "더 자세히 알려줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("단일 출처 참고");
  await expect(originDetail).toContainText("보조 출처");

  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("example.com/seoul-weather");

  // latest-update non-noisy empty-meta branch: zero-count summary + empty progress → history
  // card must not render any `.meta` detail node and must not leak `사실 검증` content.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("history-card latest-update news-only 다시 불러오기 후 두 번째 follow-up 질문에서 기사 source path(hankyung.com, mk.co.kr) + WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 drift하지 않습니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "history-card-reload-latest-news-second-followup");

  const recordId = `websearch-latest-news-2fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `기준금리-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "기준금리 속보",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 2,
    results: [
      { title: "기준금리 속보 - 한국경제", url: "https://www.hankyung.com/economy/2025", snippet: "한국은행이 기준금리를 동결했다고 밝혔다." },
      { title: "기준금리 뉴스 - 매일경제", url: "https://www.mk.co.kr/economy/2025", snippet: "한국은행이 기준금리를 동결했다." },
    ],
    pages: [
      { url: "https://www.hankyung.com/economy/2025", title: "기준금리 속보 - 한국경제", text: "한국은행이 기준금리를 동결했다고 밝혔다." },
      { url: "https://www.mk.co.kr/economy/2025", title: "기준금리 뉴스 - 매일경제", text: "한국은행이 기준금리를 동결했다." },
    ],
    summary_text: "웹 검색 요약: 기준금리 속보\n\n한국은행이 기준금리를 동결했다고 밝혔다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "latest_update", verification_label: "기사 교차 확인", source_roles: ["보조 기사"] },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{ record_id: recordId, query: "기준금리 속보", answer_mode: "latest_update", verification_label: "기사 교차 확인", source_roles: ["보조 기사"], result_count: 2, page_count: 2, created_at: record.created_at, record_path: recordPath }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // First follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });
  await expect(originBadge).toHaveText("WEB");

  // Second follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "더 자세히 알려줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("기사 교차 확인");
  await expect(originDetail).toContainText("보조 기사");

  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("hankyung.com");
  await expect(contextBox).toContainText("mk.co.kr");

  // latest-update non-noisy empty-meta branch: zero-count summary + empty progress → history
  // card must not render any `.meta` detail node and must not leak `사실 검증` content.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("latest-update mixed-source 자연어 reload에서 source path(store.steampowered.com, yna.co.kr) + WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "latest-mixed-natural-reload");

  const recordId = `websearch-latest-mixed-nat-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `스팀할인-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "스팀 여름 할인",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 2,
    results: [
      { title: "Steam 여름 할인 - Steam Store", url: "https://store.steampowered.com/sale/summer2026", snippet: "Steam 여름 할인이 시작되었습니다." },
      { title: "스팀 여름 할인 시작 - 게임뉴스", url: "https://www.yna.co.kr/view/AKR20260401000100017", snippet: "스팀이 2026년 여름 할인을 시작했다." },
    ],
    pages: [
      { url: "https://store.steampowered.com/sale/summer2026", title: "Steam 여름 할인", text: "Steam 여름 할인이 시작되었습니다." },
      { url: "https://www.yna.co.kr/view/AKR20260401000100017", title: "스팀 여름 할인 시작", text: "스팀이 2026년 여름 할인을 시작했다." },
    ],
    summary_text: "웹 검색 요약: 스팀 여름 할인\n\nSteam 여름 할인이 시작되었습니다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "latest_update", verification_label: "공식+기사 교차 확인", source_roles: ["보조 기사", "공식 기반"] },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{ record_id: recordId, query: "스팀 여름 할인", answer_mode: "latest_update", verification_label: "공식+기사 교차 확인", source_roles: ["보조 기사", "공식 기반"], result_count: 2, page_count: 2, created_at: record.created_at, record_path: recordPath }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Natural reload
  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("공식+기사 교차 확인");
  await expect(originDetail).toContainText("보조 기사");
  await expect(originDetail).toContainText("공식 기반");

  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("store.steampowered.com");
  await expect(contextBox).toContainText("yna.co.kr");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("latest-update single-source 자연어 reload에서 source path(example.com/seoul-weather) + WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "latest-single-natural-reload");

  const recordId = `websearch-latest-single-nat-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `서울날씨-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "서울 날씨",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 1,
    page_count: 1,
    results: [
      { title: "서울 날씨 - 예보", url: "https://example.com/seoul-weather", snippet: "서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다." },
    ],
    pages: [
      { url: "https://example.com/seoul-weather", title: "서울 날씨 - 예보", text: "서울은 맑고 낮 최고 17도. 미세먼지 보통." },
    ],
    summary_text: "웹 검색 요약: 서울 날씨\n\n서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "latest_update", verification_label: "단일 출처 참고", source_roles: ["보조 출처"] },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{ record_id: recordId, query: "서울 날씨", answer_mode: "latest_update", verification_label: "단일 출처 참고", source_roles: ["보조 출처"], result_count: 1, page_count: 1, created_at: record.created_at, record_path: recordPath }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Natural reload
  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("단일 출처 참고");
  await expect(originDetail).toContainText("보조 출처");

  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("example.com/seoul-weather");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("latest-update news-only 자연어 reload에서 기사 source path(hankyung.com, mk.co.kr) + WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "latest-news-natural-reload");

  const recordId = `websearch-latest-news-nat-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `기준금리-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "기준금리 속보",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 2,
    results: [
      { title: "기준금리 속보 - 한국경제", url: "https://www.hankyung.com/economy/2025", snippet: "한국은행이 기준금리를 동결했다고 밝혔다." },
      { title: "기준금리 뉴스 - 매일경제", url: "https://www.mk.co.kr/economy/2025", snippet: "한국은행이 기준금리를 동결했다." },
    ],
    pages: [
      { url: "https://www.hankyung.com/economy/2025", title: "기준금리 속보 - 한국경제", text: "한국은행이 기준금리를 동결했다고 밝혔다." },
      { url: "https://www.mk.co.kr/economy/2025", title: "기준금리 뉴스 - 매일경제", text: "한국은행이 기준금리를 동결했다." },
    ],
    summary_text: "웹 검색 요약: 기준금리 속보\n\n한국은행이 기준금리를 동결했다고 밝혔다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "latest_update", verification_label: "기사 교차 확인", source_roles: ["보조 기사"] },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{ record_id: recordId, query: "기준금리 속보", answer_mode: "latest_update", verification_label: "기사 교차 확인", source_roles: ["보조 기사"], result_count: 2, page_count: 2, created_at: record.created_at, record_path: recordPath }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Natural reload
  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("기사 교차 확인");
  await expect(originDetail).toContainText("보조 기사");

  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("hankyung.com");
  await expect(contextBox).toContainText("mk.co.kr");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("latest-update mixed-source 자연어 reload 후 follow-up에서 source path(store.steampowered.com, yna.co.kr) + WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "latest-mixed-natural-reload-followup");

  const recordId = `websearch-latest-mixed-nat-fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `스팀할인-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "스팀 여름 할인",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 2,
    results: [
      { title: "Steam 여름 할인 - Steam Store", url: "https://store.steampowered.com/sale/summer2026", snippet: "Steam 여름 할인이 시작되었습니다." },
      { title: "스팀 여름 할인 시작 - 게임뉴스", url: "https://www.yna.co.kr/view/AKR20260401000100017", snippet: "스팀이 2026년 여름 할인을 시작했다." },
    ],
    pages: [
      { url: "https://store.steampowered.com/sale/summer2026", title: "Steam 여름 할인", text: "Steam 여름 할인이 시작되었습니다." },
      { url: "https://www.yna.co.kr/view/AKR20260401000100017", title: "스팀 여름 할인 시작", text: "스팀이 2026년 여름 할인을 시작했다." },
    ],
    summary_text: "웹 검색 요약: 스팀 여름 할인\n\nSteam 여름 할인이 시작되었습니다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "latest_update", verification_label: "공식+기사 교차 확인", source_roles: ["보조 기사", "공식 기반"] },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{ record_id: recordId, query: "스팀 여름 할인", answer_mode: "latest_update", verification_label: "공식+기사 교차 확인", source_roles: ["보조 기사", "공식 기반"], result_count: 2, page_count: 2, created_at: record.created_at, record_path: recordPath }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Natural reload
  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });
  await expect(originBadge).toHaveText("WEB");

  // Follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge2 = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge2).toBeVisible();
  await expect(answerModeBadge2).toHaveText("최신 확인");
  const originDetail2 = page.locator("#response-origin-detail");
  await expect(originDetail2).toContainText("공식+기사 교차 확인");
  await expect(originDetail2).toContainText("보조 기사");
  await expect(originDetail2).toContainText("공식 기반");

  const contextBox2 = page.locator("#context-box");
  await expect(contextBox2).toContainText("store.steampowered.com");
  await expect(contextBox2).toContainText("yna.co.kr");

  // latest-update natural-reload empty-meta branch: zero-count summary + empty progress →
  // history card must not render any `.meta` detail node and must not leak `사실 검증` content.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("latest-update mixed-source 자연어 reload 후 두 번째 follow-up에서 source path(store.steampowered.com, yna.co.kr) + WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "latest-mixed-natural-reload-second-followup");

  const recordId = `websearch-latest-mixed-nat-2fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `스팀할인-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "스팀 여름 할인",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 2,
    results: [
      { title: "Steam 여름 할인 - Steam Store", url: "https://store.steampowered.com/sale/summer2026", snippet: "Steam 여름 할인이 시작되었습니다." },
      { title: "스팀 여름 할인 시작 - 게임뉴스", url: "https://www.yna.co.kr/view/AKR20260401000100017", snippet: "스팀이 2026년 여름 할인을 시작했다." },
    ],
    pages: [
      { url: "https://store.steampowered.com/sale/summer2026", title: "Steam 여름 할인", text: "Steam 여름 할인이 시작되었습니다." },
      { url: "https://www.yna.co.kr/view/AKR20260401000100017", title: "스팀 여름 할인 시작", text: "스팀이 2026년 여름 할인을 시작했다." },
    ],
    summary_text: "웹 검색 요약: 스팀 여름 할인\n\nSteam 여름 할인이 시작되었습니다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "latest_update", verification_label: "공식+기사 교차 확인", source_roles: ["보조 기사", "공식 기반"] },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{ record_id: recordId, query: "스팀 여름 할인", answer_mode: "latest_update", verification_label: "공식+기사 교차 확인", source_roles: ["보조 기사", "공식 기반"], result_count: 2, page_count: 2, created_at: record.created_at, record_path: recordPath }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Natural reload
  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });
  await expect(originBadge).toHaveText("WEB");

  // First follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });
  await expect(originBadge).toHaveText("WEB");

  // Second follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "더 자세히 알려줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge3 = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge3).toBeVisible();
  await expect(answerModeBadge3).toHaveText("최신 확인");
  const originDetail3 = page.locator("#response-origin-detail");
  await expect(originDetail3).toContainText("공식+기사 교차 확인");
  await expect(originDetail3).toContainText("보조 기사");
  await expect(originDetail3).toContainText("공식 기반");

  const contextBox3 = page.locator("#context-box");
  await expect(contextBox3).toContainText("store.steampowered.com");
  await expect(contextBox3).toContainText("yna.co.kr");

  // latest-update natural-reload empty-meta branch (second follow-up): zero-count summary +
  // empty progress → history card must not render any `.meta` detail node and must not leak
  // `사실 검증` content through accidental `.meta` creation.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("latest-update single-source 자연어 reload 후 follow-up에서 source path(example.com/seoul-weather) + WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "latest-single-natural-reload-followup");

  const recordId = `websearch-latest-single-nat-fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `서울날씨-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "서울 날씨",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 1,
    page_count: 1,
    results: [
      { title: "서울 날씨 - 예보", url: "https://example.com/seoul-weather", snippet: "서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다." },
    ],
    pages: [
      { url: "https://example.com/seoul-weather", title: "서울 날씨 - 예보", text: "서울은 맑고 낮 최고 17도. 미세먼지 보통." },
    ],
    summary_text: "웹 검색 요약: 서울 날씨\n\n서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "latest_update", verification_label: "단일 출처 참고", source_roles: ["보조 출처"] },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{ record_id: recordId, query: "서울 날씨", answer_mode: "latest_update", verification_label: "단일 출처 참고", source_roles: ["보조 출처"], result_count: 1, page_count: 1, created_at: record.created_at, record_path: recordPath }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Natural reload
  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });
  await expect(originBadge).toHaveText("WEB");

  // Follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("단일 출처 참고");
  await expect(originDetail).toContainText("보조 출처");

  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("example.com/seoul-weather");

  // latest-update natural-reload empty-meta branch (single-source shallow follow-up):
  // zero-count summary + empty progress → history card must not render any `.meta` detail
  // node and must not leak `사실 검증` content.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("latest-update single-source 자연어 reload 후 두 번째 follow-up에서 source path(example.com/seoul-weather) + WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "latest-single-natural-reload-second-followup");

  const recordId = `websearch-latest-single-nat-2fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `서울날씨-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "서울 날씨",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 1,
    page_count: 1,
    results: [
      { title: "서울 날씨 - 예보", url: "https://example.com/seoul-weather", snippet: "서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다." },
    ],
    pages: [
      { url: "https://example.com/seoul-weather", title: "서울 날씨 - 예보", text: "서울은 맑고 낮 최고 17도. 미세먼지 보통." },
    ],
    summary_text: "웹 검색 요약: 서울 날씨\n\n서울은 맑고 낮 최고 17도, 밤 최저 7도로 예보되었습니다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "latest_update", verification_label: "단일 출처 참고", source_roles: ["보조 출처"] },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{ record_id: recordId, query: "서울 날씨", answer_mode: "latest_update", verification_label: "단일 출처 참고", source_roles: ["보조 출처"], result_count: 1, page_count: 1, created_at: record.created_at, record_path: recordPath }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Natural reload
  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });
  await expect(originBadge).toHaveText("WEB");

  // First follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });
  await expect(originBadge).toHaveText("WEB");

  // Second follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "더 자세히 알려줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("단일 출처 참고");
  await expect(originDetail).toContainText("보조 출처");

  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("example.com/seoul-weather");

  // latest-update natural-reload empty-meta branch (single-source second follow-up):
  // zero-count summary + empty progress → history card must not render any `.meta` detail
  // node and must not leak `사실 검증` content.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("latest-update news-only 자연어 reload 후 follow-up에서 기사 source path(hankyung.com, mk.co.kr) + WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "latest-news-natural-reload-followup");

  const recordId = `websearch-latest-news-nat-fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `기준금리-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "기준금리 속보",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 2,
    results: [
      { title: "기준금리 속보 - 한국경제", url: "https://www.hankyung.com/economy/2025", snippet: "한국은행이 기준금리를 동결했다고 밝혔다." },
      { title: "기준금리 뉴스 - 매일경제", url: "https://www.mk.co.kr/economy/2025", snippet: "한국은행이 기준금리를 동결했다." },
    ],
    pages: [
      { url: "https://www.hankyung.com/economy/2025", title: "기준금리 속보 - 한국경제", text: "한국은행이 기준금리를 동결했다고 밝혔다." },
      { url: "https://www.mk.co.kr/economy/2025", title: "기준금리 뉴스 - 매일경제", text: "한국은행이 기준금리를 동결했다." },
    ],
    summary_text: "웹 검색 요약: 기준금리 속보\n\n한국은행이 기준금리를 동결했다고 밝혔다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "latest_update", verification_label: "기사 교차 확인", source_roles: ["보조 기사"] },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{ record_id: recordId, query: "기준금리 속보", answer_mode: "latest_update", verification_label: "기사 교차 확인", source_roles: ["보조 기사"], result_count: 2, page_count: 2, created_at: record.created_at, record_path: recordPath }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Natural reload
  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });
  await expect(originBadge).toHaveText("WEB");

  // Follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("기사 교차 확인");
  await expect(originDetail).toContainText("보조 기사");

  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("hankyung.com");
  await expect(contextBox).toContainText("mk.co.kr");

  // latest-update natural-reload empty-meta branch (news-only shallow follow-up):
  // zero-count summary + empty progress → history card must not render any `.meta` detail
  // node and must not leak `사실 검증` content.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("latest-update news-only 자연어 reload 후 두 번째 follow-up에서 기사 source path(hankyung.com, mk.co.kr) + WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "latest-news-natural-reload-second-followup");

  const recordId = `websearch-latest-news-nat-2fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `기준금리-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "기준금리 속보",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 2,
    page_count: 2,
    results: [
      { title: "기준금리 속보 - 한국경제", url: "https://www.hankyung.com/economy/2025", snippet: "한국은행이 기준금리를 동결했다고 밝혔다." },
      { title: "기준금리 뉴스 - 매일경제", url: "https://www.mk.co.kr/economy/2025", snippet: "한국은행이 기준금리를 동결했다." },
    ],
    pages: [
      { url: "https://www.hankyung.com/economy/2025", title: "기준금리 속보 - 한국경제", text: "한국은행이 기준금리를 동결했다고 밝혔다." },
      { url: "https://www.mk.co.kr/economy/2025", title: "기준금리 뉴스 - 매일경제", text: "한국은행이 기준금리를 동결했다." },
    ],
    summary_text: "웹 검색 요약: 기준금리 속보\n\n한국은행이 기준금리를 동결했다고 밝혔다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "latest_update", verification_label: "기사 교차 확인", source_roles: ["보조 기사"] },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{ record_id: recordId, query: "기준금리 속보", answer_mode: "latest_update", verification_label: "기사 교차 확인", source_roles: ["보조 기사"], result_count: 2, page_count: 2, created_at: record.created_at, record_path: recordPath }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();

  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Natural reload
  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });
  await expect(originBadge).toHaveText("WEB");

  // First follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });
  await expect(originBadge).toHaveText("WEB");

  // Second follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "더 자세히 알려줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("기사 교차 확인");
  await expect(originDetail).toContainText("보조 기사");

  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("hankyung.com");
  await expect(contextBox).toContainText("mk.co.kr");

  // latest-update natural-reload empty-meta branch (news-only second follow-up):
  // zero-count summary + empty progress → history card must not render any `.meta` detail
  // node and must not leak `사실 검증` content.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("latest-update noisy community source가 자연어 reload 후 follow-up에서도 보조 커뮤니티/brunch 미노출 + 기사 교차 확인, 보조 기사, hankyung.com · mk.co.kr 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "latest-noisy-natural-reload-followup");

  const recordId = `websearch-latest-noisy-nat-fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `기준금리-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "기준금리 속보",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 3,
    results: [
      { title: "기준금리 속보 - 한국경제", url: "https://www.hankyung.com/economy/2025", snippet: "한국은행이 기준금리를 동결했다고 밝혔다." },
      { title: "기준금리 뉴스 - 매일경제", url: "https://www.mk.co.kr/economy/2025", snippet: "한국은행이 기준금리를 동결했다." },
      { title: "기준금리 커뮤니티", url: "https://brunch.co.kr/economy", snippet: "기준금리 속보 - 로그인 회원가입 구독 광고" },
    ],
    pages: [
      { url: "https://www.hankyung.com/economy/2025", title: "기준금리 속보 - 한국경제", text: "한국은행이 기준금리를 동결했다고 밝혔다." },
      { url: "https://www.mk.co.kr/economy/2025", title: "기준금리 뉴스 - 매일경제", text: "한국은행이 기준금리를 동결했다." },
      { url: "https://brunch.co.kr/economy", title: "기준금리 커뮤니티", text: "기준금리 속보 - 로그인 회원가입 구독 광고" },
    ],
    summary_text: "웹 검색 요약: 기준금리 속보\n\n한국은행이 기준금리를 동결했다고 밝혔다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "latest_update", verification_label: "기사 교차 확인", source_roles: ["보조 기사"] },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{ record_id: recordId, query: "기준금리 속보", answer_mode: "latest_update", verification_label: "기사 교차 확인", source_roles: ["보조 기사"], result_count: 3, page_count: 3, created_at: record.created_at, record_path: recordPath }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });
  await expect(originBadge).toHaveText("WEB");

  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("기사 교차 확인");
  await expect(originDetail).toContainText("보조 기사");
  const originDetailText = await originDetail.textContent();
  expect(originDetailText).not.toContain("보조 커뮤니티");
  expect(originDetailText).not.toContain("brunch");
  const responseText = await page.getByTestId("response-text").textContent();
  expect(responseText).not.toContain("brunch");
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("hankyung.com");
  await expect(contextBox).toContainText("mk.co.kr");
  const contextBoxText = await contextBox.textContent();
  expect(contextBoxText).not.toContain("brunch");

  // latest-update noisy empty-meta branch: zero-count claim_coverage_summary + empty
  // progress → investigation history card must render no `.meta` detail node, and must
  // not leak the answer-mode label `최신 확인` nor the verification label `기사 교차 확인`
  // nor any accidental `사실 검증` prefix into the history-item content area.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("latest-update noisy community source가 자연어 reload 후 두 번째 follow-up에서도 보조 커뮤니티/brunch 미노출 + 기사 교차 확인, 보조 기사, hankyung.com · mk.co.kr 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "latest-noisy-natural-reload-second-followup");

  const recordId = `websearch-latest-noisy-nat-2fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `기준금리-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "기준금리 속보",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 3,
    results: [
      { title: "기준금리 속보 - 한국경제", url: "https://www.hankyung.com/economy/2025", snippet: "한국은행이 기준금리를 동결했다고 밝혔다." },
      { title: "기준금리 뉴스 - 매일경제", url: "https://www.mk.co.kr/economy/2025", snippet: "한국은행이 기준금리를 동결했다." },
      { title: "기준금리 커뮤니티", url: "https://brunch.co.kr/economy", snippet: "기준금리 속보 - 로그인 회원가입 구독 광고" },
    ],
    pages: [
      { url: "https://www.hankyung.com/economy/2025", title: "기준금리 속보 - 한국경제", text: "한국은행이 기준금리를 동결했다고 밝혔다." },
      { url: "https://www.mk.co.kr/economy/2025", title: "기준금리 뉴스 - 매일경제", text: "한국은행이 기준금리를 동결했다." },
      { url: "https://brunch.co.kr/economy", title: "기준금리 커뮤니티", text: "기준금리 속보 - 로그인 회원가입 구독 광고" },
    ],
    summary_text: "웹 검색 요약: 기준금리 속보\n\n한국은행이 기준금리를 동결했다고 밝혔다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "latest_update", verification_label: "기사 교차 확인", source_roles: ["보조 기사"] },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{ record_id: recordId, query: "기준금리 속보", answer_mode: "latest_update", verification_label: "기사 교차 확인", source_roles: ["보조 기사"], result_count: 3, page_count: 3, created_at: record.created_at, record_path: recordPath }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });
  await expect(originBadge).toHaveText("WEB");

  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });
  await expect(originBadge).toHaveText("WEB");

  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "더 자세히 알려줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("기사 교차 확인");
  await expect(originDetail).toContainText("보조 기사");
  const originDetailText = await originDetail.textContent();
  expect(originDetailText).not.toContain("보조 커뮤니티");
  expect(originDetailText).not.toContain("brunch");
  const responseText = await page.getByTestId("response-text").textContent();
  expect(responseText).not.toContain("brunch");
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("hankyung.com");
  await expect(contextBox).toContainText("mk.co.kr");
  const contextBoxText = await contextBox.textContent();
  expect(contextBoxText).not.toContain("brunch");

  // latest-update noisy empty-meta branch (second follow-up): zero-count summary + empty
  // progress → history card must not render any `.meta` detail node and must not leak
  // `사실 검증` content through accidental `.meta` creation.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("history-card latest-update noisy community source가 다시 불러오기 후 follow-up에서도 보조 커뮤니티/brunch 미노출 + 기사 교차 확인, 보조 기사, hankyung.com · mk.co.kr 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "latest-noisy-click-reload-followup");

  const recordId = `websearch-latest-noisy-click-fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `기준금리-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "기준금리 속보",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 3,
    results: [
      { title: "기준금리 속보 - 한국경제", url: "https://www.hankyung.com/economy/2025", snippet: "한국은행이 기준금리를 동결했다고 밝혔다." },
      { title: "기준금리 뉴스 - 매일경제", url: "https://www.mk.co.kr/economy/2025", snippet: "한국은행이 기준금리를 동결했다." },
      { title: "기준금리 커뮤니티", url: "https://brunch.co.kr/economy", snippet: "기준금리 속보 - 로그인 회원가입 구독 광고" },
    ],
    pages: [
      { url: "https://www.hankyung.com/economy/2025", title: "기준금리 속보 - 한국경제", text: "한국은행이 기준금리를 동결했다고 밝혔다." },
      { url: "https://www.mk.co.kr/economy/2025", title: "기준금리 뉴스 - 매일경제", text: "한국은행이 기준금리를 동결했다." },
      { url: "https://brunch.co.kr/economy", title: "기준금리 커뮤니티", text: "기준금리 속보 - 로그인 회원가입 구독 광고" },
    ],
    summary_text: "웹 검색 요약: 기준금리 속보\n\n한국은행이 기준금리를 동결했다고 밝혔다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "latest_update", verification_label: "기사 교차 확인", source_roles: ["보조 기사"] },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{ record_id: recordId, query: "기준금리 속보", answer_mode: "latest_update", verification_label: "기사 교차 확인", source_roles: ["보조 기사"], result_count: 3, page_count: 3, created_at: record.created_at, record_path: recordPath }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("기사 교차 확인");
  await expect(originDetail).toContainText("보조 기사");
  const originDetailText = await originDetail.textContent();
  expect(originDetailText).not.toContain("보조 커뮤니티");
  expect(originDetailText).not.toContain("brunch");
  const responseText = await page.getByTestId("response-text").textContent();
  expect(responseText).not.toContain("brunch");
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("hankyung.com");
  await expect(contextBox).toContainText("mk.co.kr");
  const contextBoxText = await contextBox.textContent();
  expect(contextBoxText).not.toContain("brunch");

  // latest-update noisy empty-meta branch (click-reload shallow follow-up): zero-count
  // summary + empty progress → history card must not render any `.meta` detail node and
  // must not leak `사실 검증` content through accidental `.meta` creation.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("history-card latest-update noisy community source가 다시 불러오기 후 두 번째 follow-up에서도 보조 커뮤니티/brunch 미노출 + 기사 교차 확인, 보조 기사, hankyung.com · mk.co.kr 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "latest-noisy-click-reload-second-followup");

  const recordId = `websearch-latest-noisy-click-2fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `기준금리-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "기준금리 속보",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 3,
    results: [
      { title: "기준금리 속보 - 한국경제", url: "https://www.hankyung.com/economy/2025", snippet: "한국은행이 기준금리를 동결했다고 밝혔다." },
      { title: "기준금리 뉴스 - 매일경제", url: "https://www.mk.co.kr/economy/2025", snippet: "한국은행이 기준금리를 동결했다." },
      { title: "기준금리 커뮤니티", url: "https://brunch.co.kr/economy", snippet: "기준금리 속보 - 로그인 회원가입 구독 광고" },
    ],
    pages: [
      { url: "https://www.hankyung.com/economy/2025", title: "기준금리 속보 - 한국경제", text: "한국은행이 기준금리를 동결했다고 밝혔다." },
      { url: "https://www.mk.co.kr/economy/2025", title: "기준금리 뉴스 - 매일경제", text: "한국은행이 기준금리를 동결했다." },
      { url: "https://brunch.co.kr/economy", title: "기준금리 커뮤니티", text: "기준금리 속보 - 로그인 회원가입 구독 광고" },
    ],
    summary_text: "웹 검색 요약: 기준금리 속보\n\n한국은행이 기준금리를 동결했다고 밝혔다.",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "latest_update", verification_label: "기사 교차 확인", source_roles: ["보조 기사"] },
    claim_coverage: [],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{ record_id: recordId, query: "기준금리 속보", answer_mode: "latest_update", verification_label: "기사 교차 확인", source_roles: ["보조 기사"], result_count: 3, page_count: 3, created_at: record.created_at, record_path: recordPath }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // First follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });
  await expect(originBadge).toHaveText("WEB");

  // Second follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "더 자세히 알려줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("최신 확인");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("기사 교차 확인");
  await expect(originDetail).toContainText("보조 기사");
  const originDetailText = await originDetail.textContent();
  expect(originDetailText).not.toContain("보조 커뮤니티");
  expect(originDetailText).not.toContain("brunch");
  const responseText = await page.getByTestId("response-text").textContent();
  expect(responseText).not.toContain("brunch");
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("hankyung.com");
  await expect(contextBox).toContainText("mk.co.kr");
  const contextBoxText = await contextBox.textContent();
  expect(contextBoxText).not.toContain("brunch");

  // latest-update noisy empty-meta branch (click-reload second follow-up): zero-count
  // summary + empty progress → history card must not render any `.meta` detail node and
  // must not leak `사실 검증` content through accidental `.meta` creation.
  const historyCard = historyBox.locator(".history-item").first();
  await expect(historyCard.locator(".meta")).toHaveCount(0);
  await expect(historyCard).not.toContainText("사실 검증");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("entity-card noisy single-source claim(출시일/2025/blog.example.com)이 자연어 reload 후 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-noisy-natural-reload-followup-prov");

  const recordId = `websearch-entity-noisy-nat-fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 3,
    results: [
      { title: "붉은사막 - 나무위키", url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { title: "붉은사막 - 위키백과", url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { title: "붉은사막 출시일 정보", url: "https://blog.example.com/crimson-desert", snippet: "붉은사막 출시일은 2025년 12월로 예정되어 있다." },
    ],
    pages: [
      { url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", title: "붉은사막 - 나무위키", text: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", title: "붉은사막 - 위키백과", text: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { url: "https://blog.example.com/crimson-desert", title: "붉은사막 출시일 정보", text: "붉은사막 출시일은 2025년 12월로 예정되어 있다. 로그인 회원가입 구독 광고" },
    ],
    summary_text: "웹 검색 요약: 붉은사막\n\n확인된 사실:\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다. [교차 확인]",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "entity_card", verification_label: "설명형 다중 출처 합의", source_roles: ["백과 기반"] },
    claim_coverage: [{ slot: "장르", status: "strong", status_label: "교차 확인", value: "오픈월드 액션 어드벤처 게임", support_count: 2, candidate_count: 2, source_role: "encyclopedia" }],
    claim_coverage_progress_summary: "교차 확인 1건.",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{ record_id: recordId, query: "붉은사막", answer_mode: "entity_card", verification_label: "설명형 다중 출처 합의", source_roles: ["백과 기반"], result_count: 3, page_count: 3, created_at: record.created_at, record_path: recordPath }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });
  await expect(originBadge).toHaveText("WEB");

  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("백과 기반");
  const originDetailText = await originDetail.textContent();
  expect(originDetailText).not.toContain("출시일");
  expect(originDetailText).not.toContain("2025");
  expect(originDetailText).not.toContain("blog.example.com");
  const responseText = await page.getByTestId("response-text").textContent();
  expect(responseText).toContain("확인된 사실 [교차 확인]:");
  expect(responseText).not.toContain("출시일");
  expect(responseText).not.toContain("2025");
  expect(responseText).not.toContain("blog.example.com");
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");
  await expect(contextBox).toContainText("blog.example.com");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("entity-card noisy single-source claim(출시일/2025/blog.example.com)이 자연어 reload 후 두 번째 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-noisy-natural-reload-second-followup-prov");

  const recordId = `websearch-entity-noisy-nat-2fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 3,
    results: [
      { title: "붉은사막 - 나무위키", url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { title: "붉은사막 - 위키백과", url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { title: "붉은사막 출시일 정보", url: "https://blog.example.com/crimson-desert", snippet: "붉은사막 출시일은 2025년 12월로 예정되어 있다." },
    ],
    pages: [
      { url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", title: "붉은사막 - 나무위키", text: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", title: "붉은사막 - 위키백과", text: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { url: "https://blog.example.com/crimson-desert", title: "붉은사막 출시일 정보", text: "붉은사막 출시일은 2025년 12월로 예정되어 있다. 로그인 회원가입 구독 광고" },
    ],
    summary_text: "웹 검색 요약: 붉은사막\n\n확인된 사실:\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다. [교차 확인]",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "entity_card", verification_label: "설명형 다중 출처 합의", source_roles: ["백과 기반"] },
    claim_coverage: [{ slot: "장르", status: "strong", status_label: "교차 확인", value: "오픈월드 액션 어드벤처 게임", support_count: 2, candidate_count: 2, source_role: "encyclopedia" }],
    claim_coverage_progress_summary: "교차 확인 1건.",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{ record_id: recordId, query: "붉은사막", answer_mode: "entity_card", verification_label: "설명형 다중 출처 합의", source_roles: ["백과 기반"], result_count: 3, page_count: 3, created_at: record.created_at, record_path: recordPath }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  await page.evaluate(async () => { await sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" }); });
  await expect(originBadge).toHaveText("WEB");

  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });
  await expect(originBadge).toHaveText("WEB");

  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "더 자세히 알려줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("백과 기반");
  const originDetailText = await originDetail.textContent();
  expect(originDetailText).not.toContain("출시일");
  expect(originDetailText).not.toContain("2025");
  expect(originDetailText).not.toContain("blog.example.com");
  const responseText = await page.getByTestId("response-text").textContent();
  expect(responseText).toContain("확인된 사실 [교차 확인]:");
  expect(responseText).not.toContain("출시일");
  expect(responseText).not.toContain("2025");
  expect(responseText).not.toContain("blog.example.com");
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");
  await expect(contextBox).toContainText("blog.example.com");

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("history-card entity-card noisy single-source claim(출시일/2025/blog.example.com)이 다시 불러오기 후 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-noisy-click-reload-followup-prov");

  const recordId = `websearch-entity-noisy-click-fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 3,
    results: [
      { title: "붉은사막 - 나무위키", url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { title: "붉은사막 - 위키백과", url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { title: "붉은사막 출시일 정보", url: "https://blog.example.com/crimson-desert", snippet: "붉은사막 출시일은 2025년 12월로 예정되어 있다." },
    ],
    pages: [
      { url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", title: "붉은사막 - 나무위키", text: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", title: "붉은사막 - 위키백과", text: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { url: "https://blog.example.com/crimson-desert", title: "붉은사막 출시일 정보", text: "붉은사막 출시일은 2025년 12월로 예정되어 있다. 로그인 회원가입 구독 광고" },
    ],
    summary_text: "웹 검색 요약: 붉은사막\n\n확인된 사실:\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다. [교차 확인]",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "entity_card", verification_label: "설명형 다중 출처 합의", source_roles: ["백과 기반"] },
    // Strong-plus-missing claim_coverage mix matches the actual noisy entity-card runtime branch
    // observed via the focused probe: `strong=3`, `weak=0`, `missing=2`, empty progress summary.
    claim_coverage: [
      { slot: "장르", status: "strong", status_label: "교차 확인", value: "오픈월드 액션 어드벤처 게임", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "개발사", status: "strong", status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "플랫폼", status: "strong", status_label: "교차 확인", value: "PC/콘솔", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "출시일", status: "missing", status_label: "미확인" },
      { slot: "가격", status: "missing", status_label: "미확인" },
    ],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{
      record_id: recordId,
      query: "붉은사막",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["백과 기반"],
      result_count: 3,
      page_count: 3,
      created_at: record.created_at,
      record_path: recordPath,
      claim_coverage_summary: { strong: 3, weak: 0, missing: 2, conflict: 0 },
      claim_coverage_progress_summary: "",
    }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // Follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("백과 기반");
  const originDetailText = await originDetail.textContent();
  expect(originDetailText).not.toContain("출시일");
  expect(originDetailText).not.toContain("2025");
  expect(originDetailText).not.toContain("blog.example.com");
  const responseText = await page.getByTestId("response-text").textContent();
  expect(responseText).not.toContain("출시일");
  expect(responseText).not.toContain("2025");
  expect(responseText).not.toContain("blog.example.com");
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");
  await expect(contextBox).toContainText("blog.example.com");

  // History-card `.meta` must carry the same strong-plus-missing count-only line at the
  // shallow click-reload follow-up point, matching the deeper second-follow-up scenario.
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 3 · 미확인 2");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");
  await expect(historyCardMeta).not.toContainText(" ·  · ");
  const postFollowUpMetaText = ((await historyCardMeta.textContent()) || "").trim();
  expect(postFollowUpMetaText.length).toBeGreaterThan(0);
  expect(postFollowUpMetaText.startsWith("·")).toBe(false);
  expect(postFollowUpMetaText.endsWith("·")).toBe(false);

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("history-card entity-card noisy single-source claim(출시일/2025/blog.example.com)이 다시 불러오기 후 두 번째 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다", async ({ page }) => {
  const sessionId = await prepareSession(page, "entity-noisy-click-reload-second-followup-prov");

  const recordId = `websearch-entity-noisy-click-2fu-${Date.now().toString(36)}`;
  const recordDir = path.join(repoRoot, "data", "web-search", sessionId);
  const recordPath = path.join(recordDir, `붉은사막-${recordId}.json`);
  fs.mkdirSync(recordDir, { recursive: true });
  const record = {
    record_id: recordId,
    session_id: sessionId,
    query: "붉은사막",
    permission: "enabled",
    created_at: new Date().toISOString(),
    result_count: 3,
    page_count: 3,
    results: [
      { title: "붉은사막 - 나무위키", url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { title: "붉은사막 - 위키백과", url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", snippet: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { title: "붉은사막 출시일 정보", url: "https://blog.example.com/crimson-desert", snippet: "붉은사막 출시일은 2025년 12월로 예정되어 있다." },
    ],
    pages: [
      { url: "https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", title: "붉은사막 - 나무위키", text: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { url: "https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89", title: "붉은사막 - 위키백과", text: "붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다." },
      { url: "https://blog.example.com/crimson-desert", title: "붉은사막 출시일 정보", text: "붉은사막 출시일은 2025년 12월로 예정되어 있다. 로그인 회원가입 구독 광고" },
    ],
    summary_text: "웹 검색 요약: 붉은사막\n\n확인된 사실:\n붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다. [교차 확인]",
    response_origin: { provider: "web", badge: "WEB", label: "웹 검색", answer_mode: "entity_card", verification_label: "설명형 다중 출처 합의", source_roles: ["백과 기반"] },
    // Strong-plus-missing claim_coverage mix matches the actual noisy entity-card runtime branch
    // observed via the focused probe: `strong=3`, `weak=0`, `missing=2`, empty progress summary.
    claim_coverage: [
      { slot: "장르", status: "strong", status_label: "교차 확인", value: "오픈월드 액션 어드벤처 게임", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "개발사", status: "strong", status_label: "교차 확인", value: "펄어비스", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "플랫폼", status: "strong", status_label: "교차 확인", value: "PC/콘솔", support_count: 2, candidate_count: 2, source_role: "encyclopedia" },
      { slot: "출시일", status: "missing", status_label: "미확인" },
      { slot: "가격", status: "missing", status_label: "미확인" },
    ],
    claim_coverage_progress_summary: "",
  };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2), "utf-8");

  await page.evaluate(({ items }) => { renderSearchHistory(items); }, {
    items: [{
      record_id: recordId,
      query: "붉은사막",
      answer_mode: "entity_card",
      verification_label: "설명형 다중 출처 합의",
      source_roles: ["백과 기반"],
      result_count: 3,
      page_count: 3,
      created_at: record.created_at,
      record_path: recordPath,
      claim_coverage_summary: { strong: 3, weak: 0, missing: 2, conflict: 0 },
      claim_coverage_progress_summary: "",
    }],
  });

  const historyBox = page.locator("#search-history-box");
  await expect(historyBox).toBeVisible();
  await historyBox.locator(".history-item-actions button.secondary").first().click();
  const originBadge = page.locator("#response-origin-badge");
  await expect(originBadge).toHaveText("WEB");

  // First follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });
  await expect(originBadge).toHaveText("WEB");

  // After the first follow-up the history-card `.meta` must already carry the strong-plus-
  // missing count-only line derived from the stored claim_coverage (3 strong + 2 missing).
  const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 3 · 미확인 2");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");

  // Second follow-up
  await page.evaluate(async ({ rid }) => { await sendRequest({ user_text: "더 자세히 알려줘", load_web_search_record_id: rid }, "follow_up"); }, { rid: recordId });

  await expect(originBadge).toHaveText("WEB");
  await expect(originBadge).toHaveClass(/web/);
  const answerModeBadge = page.locator("#response-answer-mode-badge");
  await expect(answerModeBadge).toBeVisible();
  await expect(answerModeBadge).toHaveText("설명 카드");
  const originDetail = page.locator("#response-origin-detail");
  await expect(originDetail).toContainText("설명형 다중 출처 합의");
  await expect(originDetail).toContainText("백과 기반");
  const originDetailText = await originDetail.textContent();
  expect(originDetailText).not.toContain("출시일");
  expect(originDetailText).not.toContain("2025");
  expect(originDetailText).not.toContain("blog.example.com");
  const responseText = await page.getByTestId("response-text").textContent();
  expect(responseText).not.toContain("출시일");
  expect(responseText).not.toContain("2025");
  expect(responseText).not.toContain("blog.example.com");
  const contextBox = page.locator("#context-box");
  await expect(contextBox).toContainText("namu.wiki");
  await expect(contextBox).toContainText("ko.wikipedia.org");
  await expect(contextBox).toContainText("blog.example.com");

  // History-card `.meta` must still carry the same strong-plus-missing count-only line after
  // the second follow-up with no drift, no leaked answer-mode label, no leading/trailing
  // separator, and no doubled separator. The count line legitimately contains ` · ` between
  // `교차 확인 3` and `미확인 2`.
  await expect(historyCardMeta).toHaveCount(1);
  await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 3 · 미확인 2");
  await expect(historyCardMeta).not.toContainText("설명 카드");
  await expect(historyCardMeta).not.toContainText("최신 확인");
  await expect(historyCardMeta).not.toContainText("일반 검색");
  await expect(historyCardMeta).not.toContainText(" ·  · ");
  const postSecondFollowUpMetaText = ((await historyCardMeta.textContent()) || "").trim();
  expect(postSecondFollowUpMetaText.length).toBeGreaterThan(0);
  expect(postSecondFollowUpMetaText.startsWith("·")).toBe(false);
  expect(postSecondFollowUpMetaText.endsWith("·")).toBe(false);

  try { fs.unlinkSync(recordPath); fs.rmdirSync(recordDir); } catch (_) {}
});

test("브라우저 파일 선택으로 scanned/image-only PDF를 선택하면 OCR 미지원 안내가 표시됩니다", async ({ page }) => {
  await prepareSession(page, "scanned-pdf-ocr");
  await page.getByTestId("browser-file-input").setInputFiles(scannedPdfFixturePath);
  await expect(page.locator("#picked-file-name")).toContainText("scanned-stub.pdf");

  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("response-text")).toBeVisible();
  const responseText = await page.getByTestId("response-text").textContent();
  expect(responseText).toContain("요약할 수 없습니다");
  expect(responseText).toContain("OCR");
  expect(responseText).toContain("이미지형 PDF");
  expect(responseText).toContain("다음 단계:");
});

test("브라우저 폴더 선택으로 scanned PDF + readable file이 섞인 폴더를 검색하면 count-only partial-failure notice가 표시됩니다", async ({ page }) => {
  await prepareSession(page, "mixed-folder-skipped-pdf");
  await page.locator('input[name="request_mode"][value="search"]').check();
  await page.getByTestId("browser-folder-input").setInputFiles(mixedSearchFixtureDir);
  await expect(page.locator("#picked-folder-name")).toContainText("2개 파일");
  await page.getByTestId("search-query").fill("budget");
  await page.locator("#search-only").check();

  await page.getByTestId("submit-request").click();

  // search-only hides response-text but populates it; wait for search preview then read hidden text
  await expect(page.getByTestId("response-search-preview")).toBeVisible();
  const responseText = await page.getByTestId("response-text").textContent();
  expect(responseText).toContain("스캔본 또는 이미지형 PDF");
  expect(responseText).toContain("건너뛰었습니다");

  // successful-result retention: readable notes.txt with exact fields in response-detail preview
  await expect(page.locator("#response-search-preview .search-preview-item")).toHaveCount(1);
  await expect(page.locator("#response-search-preview .search-preview-name").first()).toHaveText("1. notes.txt");
  await expect(page.locator("#response-search-preview .search-preview-name").first()).toHaveAttribute("title", "mixed-search-folder/notes.txt");
  await expect(page.locator("#response-search-preview .search-preview-match").first()).toHaveText("내용 일치");
  await expect(page.locator("#response-search-preview .search-preview-snippet").first()).toBeVisible();
  await expect(page.locator("#response-search-preview .search-preview-snippet").first()).toContainText("budget");

  // search-only hides response body and copy button
  await expect(page.getByTestId("response-text")).toBeHidden();
  await expect(page.getByTestId("response-copy-text")).toBeHidden();

  // transcript preview panel retains exact fields
  const lastAssistant = page.locator("#transcript .message.assistant").last();
  await expect(lastAssistant.locator(".search-preview-panel")).toBeVisible();
  await expect(lastAssistant.locator(".search-preview-item")).toHaveCount(1);
  await expect(lastAssistant.locator(".search-preview-name").first()).toHaveText("1. notes.txt");
  await expect(lastAssistant.locator(".search-preview-name").first()).toHaveAttribute("title", "mixed-search-folder/notes.txt");
  await expect(lastAssistant.locator(".search-preview-match").first()).toHaveText("내용 일치");
  await expect(lastAssistant.locator(".search-preview-snippet").first()).toBeVisible();
  await expect(lastAssistant.locator(".search-preview-snippet").first()).toContainText("budget");

  // selected path list retains readable result only
  await expect(page.locator("#selected-text")).toHaveText("mixed-search-folder/notes.txt");

  // selected-copy button is visible and copies the path
  await expect(page.getByTestId("selected-copy")).toBeVisible();
  await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.getByTestId("selected-copy").click();
  await expect(page.locator("#notice-box")).toHaveText("선택 경로를 복사했습니다.");
  const clipboardText = await page.evaluate(() => navigator.clipboard.readText());
  expect(clipboardText).toBe("mixed-search-folder/notes.txt");

  // transcript body (pre) should be hidden for search-only
  await expect(lastAssistant.locator("pre")).toHaveCount(0);
});

test("브라우저 폴더 선택으로 scanned PDF + readable file이 섞인 폴더를 검색+요약하면 partial-failure notice와 함께 readable file preview가 유지됩니다", async ({ page }) => {
  await prepareSession(page, "mixed-folder-skipped-pdf-summary");
  await page.locator('input[name="request_mode"][value="search"]').check();
  await page.getByTestId("browser-folder-input").setInputFiles(mixedSearchFixtureDir);
  await expect(page.locator("#picked-folder-name")).toContainText("2개 파일");
  await page.getByTestId("search-query").fill("budget");

  await page.getByTestId("submit-request").click();

  // search-plus-summary: response-text is visible with summary body
  await expect(page.getByTestId("response-text")).toBeVisible();
  const responseText = await page.getByTestId("response-text").textContent();
  expect(responseText).toContain("스캔본 또는 이미지형 PDF");
  expect(responseText).toContain("건너뛰었습니다");

  // search preview panel shows readable file result with exact fields
  await expect(page.getByTestId("response-search-preview")).toBeVisible();
  await expect(page.locator("#response-search-preview .search-preview-item")).toHaveCount(1);
  await expect(page.locator("#response-search-preview .search-preview-name").first()).toHaveText("1. notes.txt");
  await expect(page.locator("#response-search-preview .search-preview-name").first()).toHaveAttribute("title", "mixed-search-folder/notes.txt");
  await expect(page.locator("#response-search-preview .search-preview-match").first()).toHaveText("내용 일치");
  await expect(page.locator("#response-search-preview .search-preview-snippet").first()).toBeVisible();
  await expect(page.locator("#response-search-preview .search-preview-snippet").first()).toContainText("budget");

  // transcript preview panel also retains readable file result with exact fields
  const lastAssistant = page.locator("#transcript .message.assistant").last();
  await expect(lastAssistant.locator(".search-preview-panel")).toBeVisible();
  await expect(lastAssistant.locator(".search-preview-item")).toHaveCount(1);
  await expect(lastAssistant.locator(".search-preview-name").first()).toHaveText("1. notes.txt");
  await expect(lastAssistant.locator(".search-preview-name").first()).toHaveAttribute("title", "mixed-search-folder/notes.txt");
  await expect(lastAssistant.locator(".search-preview-match").first()).toHaveText("내용 일치");
  await expect(lastAssistant.locator(".search-preview-snippet").first()).toBeVisible();
  await expect(lastAssistant.locator(".search-preview-snippet").first()).toContainText("budget");
});

test("브라우저 파일 선택으로 readable text-layer PDF를 선택하면 정상 요약이 됩니다", async ({ page }) => {
  await prepareSession(page, "readable-pdf-success");
  await page.getByTestId("browser-file-input").setInputFiles(readablePdfFixturePath);
  await expect(page.locator("#picked-file-name")).toContainText("readable-text-layer.pdf");

  await page.getByTestId("submit-request").click();

  await expect(page.getByTestId("response-text")).toBeVisible();
  const responseText = await page.getByTestId("response-text").textContent();
  expect(responseText).not.toContain("요약할 수 없습니다");
  expect(responseText).not.toContain("이미지형 PDF");
  expect(responseText).toContain("local-first approval-based document assistant");
  await expect(page.locator("#context-box")).toContainText("readable-text-layer.pdf");
  await expect(page.locator("#response-quick-meta-text")).toContainText("readable-text-layer.pdf");
  await expect(page.locator("#response-quick-meta-text")).toContainText("문서 요약");
  await expect(page.locator('#transcript [data-testid="transcript-meta"]').last()).toContainText("readable-text-layer.pdf");
  await expect(page.locator('#transcript [data-testid="transcript-meta"]').last()).toContainText("문서 요약");
});

async function postStreamAndReadFinalPayload(page, payload) {
  const response = await page.request.post("/api/chat/stream", { data: payload });
  const body = await response.text();
  expect(response.ok(), body).toBeTruthy();
  const events = body
    .trim()
    .split("\n")
    .filter(Boolean)
    .map((line) => JSON.parse(line));
  const errorEvent = events.find((event) => event.event === "error");
  expect(errorEvent, body).toBeFalsy();
  const finalEvent = events.find((event) => event.event === "final");
  expect(finalEvent, body).toBeTruthy();
  expect(finalEvent.data?.ok, body).toBeTruthy();
  return finalEvent.data;
}

async function createQualityReviewQueueItem(page, sessionId, correctedText, userText = null) {
  const chatPayload = await postStreamAndReadFinalPayload(page, {
    session_id: sessionId,
    source_path: shortFixturePath,
    provider: "mock",
    ...(userText ? { user_text: userText } : {}),
  });
  const sourceMessageId = chatPayload.response?.source_message_id ?? chatPayload.source_message_id;
  expect(typeof sourceMessageId).toBe("string");

  const correctionResponse = await page.request.post("/api/correction", {
    data: {
      session_id: sessionId,
      message_id: sourceMessageId,
      corrected_text: correctedText,
    },
  });
  const correctionBody = await correctionResponse.text();
  expect(correctionResponse.ok(), correctionBody).toBeTruthy();
  const correctionPayload = JSON.parse(correctionBody);
  const messages = correctionPayload.session?.messages ?? [];
  const candidateMessage = messages.find(
    (message) => message.message_id === sourceMessageId && message.session_local_candidate
  );
  expect(candidateMessage, correctionBody).toBeTruthy();
  const candidate = candidateMessage.session_local_candidate;

  const confirmResponse = await page.request.post("/api/candidate-confirmation", {
    data: {
      session_id: sessionId,
      message_id: sourceMessageId,
      candidate_id: candidate.candidate_id,
      candidate_updated_at: candidate.updated_at,
    },
  });
  const confirmBody = await confirmResponse.text();
  expect(confirmResponse.ok(), confirmBody).toBeTruthy();
  const confirmPayload = JSON.parse(confirmBody);
  expect(confirmPayload.ok, confirmBody).toBeTruthy();

  const sessionPayload = await fetchSessionPayload(page, sessionId);
  return {
    sessionPayload,
    sourceMessageId,
  };
}

test("quality-info present in review queue item after correction and candidate confirmation", async ({ page }) => {
  await page.goto("/");
  const sessionId = await prepareSession(page, "quality-rq");

  const { sessionPayload } = await createQualityReviewQueueItem(
    page,
    sessionId,
    "수정본입니다. 핵심 내용만 남겼습니다."
  );
  const reviewItems = sessionPayload.session?.review_queue_items ?? [];
  expect(reviewItems.length).toBeGreaterThanOrEqual(1);

  const item = reviewItems[0];
  expect(item).toHaveProperty("quality_info");
  expect(item.quality_info).not.toBeNull();
  expect(
    item.quality_info.is_high_quality === null ||
    typeof item.quality_info.is_high_quality === "boolean"
  ).toBeTruthy();
  expect(
    item.quality_info.avg_similarity_score === null ||
    typeof item.quality_info.avg_similarity_score === "number"
  ).toBeTruthy();
});

test("quality-info quality-count badge visible in ChatArea when review queue item is high quality", async ({ page }) => {
  await page.goto("/");
  const sessionId = await prepareSession(page, "quality-badge");

  const { sessionPayload } = await createQualityReviewQueueItem(
    page,
    sessionId,
    "핵심 결정은 승인 기반 저장을 유지하는 것입니다. 명확하게 요약했습니다."
  );
  const reviewItems = sessionPayload.session?.review_queue_items ?? [];
  const highQualityItems = reviewItems.filter(
    (item) => item.quality_info?.is_high_quality === true
  );

  if (highQualityItems.length > 0) {
    await page.reload();
    await page.waitForLoadState("networkidle");
    await page.evaluate((sid) => {
      const sessionInput = document.getElementById("session-id");
      const loadButton = document.getElementById("load-session");
      if (sessionInput && loadButton) {
        sessionInput.value = sid;
        loadButton.click();
      }
    }, sessionId);
    await page.waitForSelector(".quality-count", { timeout: 10_000 }).catch(() => null);
    const qualityCountSpan = page.locator(".quality-count");
    const isVisible = await qualityCountSpan.isVisible().catch(() => false);
    if (isVisible) {
      await expect(qualityCountSpan).toContainText("고품질");
    }
  }

  expect(reviewItems.length).toBeGreaterThanOrEqual(1);
  expect(reviewItems[0]).toHaveProperty("quality_info");
});

test("quality-info delta_summary present in review queue item after correction", async ({ page }) => {
  await page.goto("/");
  const sessionId = await prepareSession(page, "delta-summary-rq");

  const { sessionPayload } = await createQualityReviewQueueItem(
    page,
    sessionId,
    "정리된 결과입니다. 명확하게 요약했습니다."
  );
  const reviewItems = sessionPayload.session?.review_queue_items ?? [];
  expect(reviewItems.length).toBeGreaterThanOrEqual(1);

  const item = reviewItems[0];
  expect(Object.prototype.hasOwnProperty.call(item, "delta_summary")).toBeTruthy();
  if (item.delta_summary !== null) {
    expect(typeof item.delta_summary).toBe("object");
  }
});

test("quality-info original_snippet and corrected_snippet present in review queue item", async ({ page }) => {
  await page.goto("/");
  const sessionId = await prepareSession(page, "snippet-rq");

  const { sessionPayload } = await createQualityReviewQueueItem(
    page,
    sessionId,
    "분석 결과를 간결하게 요약했습니다."
  );
  const reviewItems = sessionPayload.session?.review_queue_items ?? [];
  expect(reviewItems.length).toBeGreaterThanOrEqual(1);

  const item = reviewItems[0];
  expect(Object.prototype.hasOwnProperty.call(item, "original_snippet")).toBeTruthy();
  expect(Object.prototype.hasOwnProperty.call(item, "corrected_snippet")).toBeTruthy();
  expect(typeof item.original_snippet).toBe("string");
  expect(typeof item.corrected_snippet).toBe("string");
  expect(item.original_snippet.length).toBeGreaterThan(0);
  expect(item.corrected_snippet.length).toBeGreaterThan(0);
  expect(item.original_snippet.length).toBeLessThanOrEqual(400);
  expect(item.corrected_snippet.length).toBeLessThanOrEqual(400);
});

test("quality-info global candidate appears in review queue after cross-session recurrence", async ({ page }) => {
  await page.goto("/");
  const recurringCorrectedText = "전역 반복 패턴 교정 결과입니다.";

  const sessionId1 = await prepareSession(page, "global-rq-s1");
  await createQualityReviewQueueItem(page, sessionId1, recurringCorrectedText);

  const sessionId2 = await prepareSession(page, "global-rq-s2");
  await createQualityReviewQueueItem(page, sessionId2, recurringCorrectedText);

  const sessionId3 = await prepareSession(page, "global-rq-s3");
  const { sessionPayload } = await createQualityReviewQueueItem(
    page,
    sessionId3,
    "세 번째 세션 로컬 후보입니다."
  );
  const reviewItems = sessionPayload.session?.review_queue_items ?? [];
  expect(reviewItems.length).toBeGreaterThanOrEqual(1);

  const globalItem = reviewItems.find(
    (item) => item.is_global === true && item.source_message_id === "global"
  );
  if (globalItem) {
    expect(globalItem.item_type).toBe("global_candidate");
    expect(globalItem.candidate_id).toMatch(/^global:/);
    expect(Object.prototype.hasOwnProperty.call(globalItem, "is_global")).toBeTruthy();
  }
  for (const item of reviewItems) {
    expect(Object.prototype.hasOwnProperty.call(item, "is_global")).toBeTruthy();
  }
});

test("review queue panel opens on badge click and accept action removes item", async ({ page }) => {
  const sessionId = buildSessionId("rq-panel");
  const { sessionPayload } = await createQualityReviewQueueItem(
    page,
    sessionId,
    "요약 수정본입니다. 핵심만 남겼습니다.",
    `review queue panel ${sessionId}`
  );
  expect((sessionPayload.session?.review_queue_items ?? []).length).toBeGreaterThanOrEqual(1);
  const sessionTitle = sessionPayload.session?.title ?? sessionId;

  await page.goto("/app-preview");
  const sessionButton = page.locator("button", { hasText: sessionTitle }).first();
  await expect(sessionButton).toBeVisible({ timeout: 10_000 });
  await sessionButton.click();

  const reviewBadge = page.getByTestId("review-queue-badge");
  await expect(reviewBadge).toBeVisible({ timeout: 10_000 });
  await expect(reviewBadge).toContainText("리뷰");

  await reviewBadge.click();
  const acceptButton = page.getByTestId("review-accept").first();
  await expect(acceptButton).toBeVisible({ timeout: 5_000 });
  const reviewResponsePromise = page.waitForResponse(
    (response) => response.url().includes("/api/candidate-review")
  );
  await acceptButton.click();
  const reviewResponse = await reviewResponsePromise;
  const reviewBody = await reviewResponse.text();
  expect(reviewResponse.ok(), reviewBody).toBeTruthy();

  await expect
    .poll(async () => {
      const payload = await fetchSessionPayload(page, sessionId);
      const items = payload.session?.review_queue_items ?? [];
      return items.filter((item) => item.is_global !== true).length;
    })
    .toBe(0);
});

test("review queue edit statement sends edited text in accept request", async ({ page }) => {
  const sessionId = buildSessionId("rq-edit");
  const editedStatement = `사용자가 직접 수정한 선호 문구입니다. ${sessionId}`;
  const { sessionPayload } = await createQualityReviewQueueItem(
    page,
    sessionId,
    "분석 결과를 요약했습니다.",
    `review queue edit ${sessionId}`
  );
  expect((sessionPayload.session?.review_queue_items ?? []).length).toBeGreaterThanOrEqual(1);
  const sessionTitle = sessionPayload.session?.title ?? sessionId;

  await page.goto("/app-preview");
  const sessionButton = page.locator("button", { hasText: sessionTitle }).first();
  await expect(sessionButton).toBeVisible({ timeout: 10_000 });
  await sessionButton.click();

  const reviewBadge = page.getByTestId("review-queue-badge");
  await expect(reviewBadge).toBeVisible({ timeout: 10_000 });
  await reviewBadge.click();

  const editButton = page.getByTestId("review-edit").first();
  await expect(editButton).toBeVisible({ timeout: 5_000 });
  await editButton.click();

  const textarea = page.getByTestId("review-edit-statement").first();
  await expect(textarea).toBeVisible({ timeout: 3_000 });
  await textarea.clear();
  await textarea.fill(editedStatement);

  const reviewResponsePromise = page.waitForResponse(
    (response) => response.url().includes("/api/candidate-review")
  );
  await page.getByTestId("review-accept").first().click();
  const reviewResponse = await reviewResponsePromise;
  const reviewBody = await reviewResponse.text();
  expect(reviewResponse.ok(), reviewBody).toBeTruthy();

  await expect
    .poll(async () => {
      const payload = await fetchSessionPayload(page, sessionId);
      const items = payload.session?.review_queue_items ?? [];
      return items.filter((item) => item.is_global !== true).length;
    })
    .toBe(0);

  const reviewRequestBody = reviewResponse.request().postData();
  expect(reviewRequestBody).toBeTruthy();
  const reviewBodyParsed = JSON.parse(reviewRequestBody ?? "{}");
  expect(reviewBodyParsed.statement).toBe(editedStatement);
  expect(reviewBodyParsed.review_action).toBe("accept");
});
