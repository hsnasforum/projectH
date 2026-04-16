import { test, expect } from "@playwright/test";

test.describe("controller office smoke", () => {
  test("controller shows storage unavailable indicator when browser storage is blocked", async ({
    page,
  }) => {
    // Block localStorage before page loads so PrefStore._probe() will fail.
    // Override Storage.prototype methods to throw, matching real blocked-storage
    // behavior in restrictive browser environments (e.g. private browsing).
    await page.addInitScript(() => {
      Storage.prototype.setItem = function () {
        throw new DOMException("storage is blocked", "SecurityError");
      };
      Storage.prototype.getItem = function () {
        throw new DOMException("storage is blocked", "SecurityError");
      };
      Storage.prototype.removeItem = function () {
        throw new DOMException("storage is blocked", "SecurityError");
      };
    });

    await page.goto("/controller");

    // The toolbar storage-warn chip should be visible
    const chip = page.locator("#storage-warn");
    await expect(chip).toBeVisible();
    await expect(chip).toHaveText("⚠ 설정 비저장");

    // Tooltip should explain the situation
    await expect(chip).toHaveAttribute(
      "title",
      "localStorage 사용 불가 — 새로고침 시 toolbar 설정이 초기화됩니다",
    );

    // Event log should contain the one-time storage warning
    const warnMsg = "환경 설정 저장 불가 — 새로고침 시 toolbar 설정이 초기화됩니다";
    const eventMsgs = page.locator("#event-list .event-msg");
    const matchingMsgs = eventMsgs.filter({ hasText: warnMsg });
    await expect(matchingMsgs).toHaveCount(1);
  });

  test("controller hides storage indicator when browser storage is available", async ({
    page,
  }) => {
    await page.goto("/controller");

    // With normal localStorage, the chip should be hidden
    const chip = page.locator("#storage-warn");
    await expect(chip).toBeHidden();

    // Event log should not contain the storage warning
    const warnMsg = "환경 설정 저장 불가 — 새로고침 시 toolbar 설정이 초기화됩니다";
    const matchingMsgs = page.locator("#event-list .event-msg").filter({ hasText: warnMsg });
    await expect(matchingMsgs).toHaveCount(0);
  });

  test("agent cards expose data-fatigue attribute for fatigue observability", async ({
    page,
  }) => {
    // Stub the API to return one working agent so the sidebar renders a card
    await page.route("**/api/runtime/status", (route) =>
      route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          runtime_state: "RUNNING",
          lanes: [
            { name: "Claude", state: "working", note: "implementing slice" },
          ],
          control: {},
          watcher: { alive: true },
          artifacts: {},
        }),
      }),
    );

    await page.goto("/controller");

    // Wait for the first poll to render agent cards
    const card = page.locator('.agent-card[data-agent="Claude"]');
    await expect(card).toBeVisible();

    // The data-fatigue attribute should exist (empty string = not fatigued yet)
    await expect(card).toHaveAttribute("data-fatigue", "");

    // No fatigue indicator text should be visible initially
    const fatigueEl = card.locator(".agent-fatigue");
    await expect(fatigueEl).toHaveCount(0);
  });

  test("setAgentFatigue hook transitions card to fatigued state", async ({
    page,
  }) => {
    await page.route("**/api/runtime/status", (route) =>
      route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          runtime_state: "RUNNING",
          lanes: [
            { name: "Claude", state: "working", note: "implementing slice" },
          ],
          control: {},
          watcher: { alive: true },
          artifacts: {},
        }),
      }),
    );

    await page.goto("/controller");

    const card = page.locator('.agent-card[data-agent="Claude"]');
    await expect(card).toBeVisible();

    // Inject fatigued state via test hook
    await page.evaluate(() => window.setAgentFatigue("Claude", "fatigued"));

    await expect(card).toHaveAttribute("data-fatigue", "fatigued");
    const fatigueEl = card.locator(".agent-fatigue");
    await expect(fatigueEl).toBeVisible();
    await expect(fatigueEl).toHaveText("💦 피로 누적");
  });

  test("setAgentFatigue hook transitions card to coffee state", async ({
    page,
  }) => {
    await page.route("**/api/runtime/status", (route) =>
      route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          runtime_state: "RUNNING",
          lanes: [
            { name: "Claude", state: "working", note: "implementing slice" },
          ],
          control: {},
          watcher: { alive: true },
          artifacts: {},
        }),
      }),
    );

    await page.goto("/controller");

    const card = page.locator('.agent-card[data-agent="Claude"]');
    await expect(card).toBeVisible();

    // Inject coffee state via test hook
    await page.evaluate(() => window.setAgentFatigue("Claude", "coffee"));

    await expect(card).toHaveAttribute("data-fatigue", "coffee");
    const fatigueEl = card.locator(".agent-fatigue");
    await expect(fatigueEl).toBeVisible();
    await expect(fatigueEl).toHaveText("☕ 커피 충전 중");
  });
});
