import { test, expect } from "@playwright/test";

test.describe("controller office smoke", () => {
  test("controller shows storage unavailable indicator when browser storage is blocked", async ({
    page,
  }) => {
    // Block localStorage before page loads so PrefStore._probe() will fail.
    await page.addInitScript(() => {
      window.__storageBlocked = true;
      const origSetItem = Storage.prototype.setItem;
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

    // Debug: check if init script ran
    const blocked = await page.evaluate(() => window.__storageBlocked);
    console.log("Init script ran:", blocked);
    const probeResult = await page.evaluate(() => {
      try { localStorage.setItem("x","1"); return "no throw"; } catch(e) { return "threw: " + e.message; }
    })
    console.log("localStorage.setItem result:", probeResult);

    // The toolbar storage-warn chip should be visible
    const chip = page.locator("#storage-warn");
    await expect(chip).toBeVisible();
    await expect(chip).toHaveText("⚠ 설정 비저장");

    // Tooltip should explain the situation
    await expect(chip).toHaveAttribute(
      "title",
      "localStorage 사용 불가 — 새로고침 시 toolbar 설정이 초기화됩니다",
    );
  });

  test("controller hides storage indicator when browser storage is available", async ({
    page,
  }) => {
    await page.goto("/controller");

    // With normal localStorage, the chip should be hidden
    const chip = page.locator("#storage-warn");
    await expect(chip).toBeHidden();
  });
});
