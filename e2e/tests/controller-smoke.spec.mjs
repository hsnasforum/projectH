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

  test("idle roam targets stay within walkable bounds and outside desk exclusion rects", async ({
    page,
  }) => {
    // Stub the API to return one idle agent so the roam system is active
    await page.route("**/api/runtime/status", (route) =>
      route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          runtime_state: "RUNNING",
          lanes: [
            { name: "Claude", state: "idle", note: "" },
          ],
          control: {},
          watcher: { alive: true },
          artifacts: {},
        }),
      }),
    );

    await page.goto("/controller");

    // Wait for the first poll to populate the agents map
    const card = page.locator('.agent-card[data-agent="Claude"]');
    await expect(card).toBeVisible();

    // Read bounds constants from the controller
    const bounds = await page.evaluate(() => window.getRoamBounds());

    // Force 30 idle roam picks and collect the coordinates
    const points = await page.evaluate(() => window.testPickIdleTargets("Claude", 30));
    expect(points.length).toBe(30);

    for (const pt of points) {
      // Must be within walkable bounds
      expect(pt.x).toBeGreaterThanOrEqual(bounds.walkable.xMin);
      expect(pt.x).toBeLessThanOrEqual(bounds.walkable.xMax);
      expect(pt.y).toBeGreaterThanOrEqual(bounds.walkable.yMin);
      expect(pt.y).toBeLessThanOrEqual(bounds.walkable.yMax);

      // Must not be inside any desk exclusion rect
      for (const desk of bounds.desks) {
        const insideDesk =
          pt.x > desk.x && pt.x < desk.x + desk.w &&
          pt.y > desk.y && pt.y < desk.y + desk.h;
        expect(insideDesk).toBe(false);
      }
    }
  });

  test("idle roam avoids proximity to other idle agents (anti-stacking)", async ({
    page,
  }) => {
    await page.route("**/api/runtime/status", (route) =>
      route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          runtime_state: "RUNNING",
          lanes: [
            { name: "Claude", state: "idle", note: "" },
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

    // Place a phantom idle agent at the center of the walkable area
    const bounds = await page.evaluate(() => window.getRoamBounds());
    const centerX = (bounds.walkable.xMin + bounds.walkable.xMax) / 2;
    const centerY = (bounds.walkable.yMin + bounds.walkable.yMax) / 2;

    const results = await page.evaluate(
      ({ cx, cy }) => window.testAntiStacking("Claude", cx, cy, 50),
      { cx: centerX, cy: centerY },
    );
    expect(results.length).toBe(50);

    // Free-walk path has hard 50px exclusion; spot-based has soft scoring penalty.
    // The vast majority of picks should be >50px from the phantom agent.
    const closeCount = results.filter((r) => r.distFromOther < 50).length;
    expect(closeCount).toBeLessThan(results.length * 0.15);
  });

  test("idle roam deprioritizes recently visited spots via _roamHistory penalty", async ({
    page,
  }) => {
    await page.route("**/api/runtime/status", (route) =>
      route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          runtime_state: "RUNNING",
          lanes: [
            { name: "Claude", state: "idle", note: "" },
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

    // Pre-fill history with spots 0-4 (index 0 = most recent = most penalized at -150)
    const results = await page.evaluate(() =>
      window.testHistoryPenalty("Claude", [0, 1, 2, 3, 4], 120),
    );

    // Only spot-based picks are returned (free-walk picks excluded)
    expect(results.length).toBeGreaterThan(15);

    // The most-penalized spot (index 0, -150 penalty) should be very rarely chosen
    const mostPenalizedCount = results.filter((r) => r.spotIndex === 0).length;
    expect(mostPenalizedCount).toBeLessThan(results.length * 0.1);
  });
});
