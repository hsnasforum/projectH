import { test, expect } from "@playwright/test";

async function disableRuntimeMonitor(page) {
  await page.addInitScript(() => {
    window.__officeRuntimeMonitorDisabled = true;
  });
}

test.describe("controller office smoke", () => {
  test("cozy runtime loads from shared /controller-assets/js/cozy.js module", async ({
    page,
  }) => {
    await page.goto("/controller");
    const moduleScripts = await page.evaluate(() =>
      Array.from(document.querySelectorAll("script"))
        .map((el) => el.getAttribute("src") || "")
        .filter((src) => src.includes("/controller-assets/js/cozy.js")),
    );
    expect(moduleScripts.length).toBe(1);
    // Runtime globals exposed by cozy.js must be reachable on window.
    const hasGlobals = await page.evaluate(() => ({
      getRoamBounds: typeof window.getRoamBounds === "function",
      setAgentFatigue: typeof window.setAgentFatigue === "function",
      testPickIdleTargets: typeof window.testPickIdleTargets === "function",
      testAntiStacking: typeof window.testAntiStacking === "function",
      testHistoryPenalty: typeof window.testHistoryPenalty === "function",
    }));
    expect(hasGlobals.getRoamBounds).toBe(true);
    expect(hasGlobals.setAgentFatigue).toBe(true);
    expect(hasGlobals.testPickIdleTargets).toBe(true);
    expect(hasGlobals.testAntiStacking).toBe(true);
    expect(hasGlobals.testHistoryPenalty).toBe(true);
  });

  test("cozy scene exposes window/tube/cat/audio feature hooks from the shared runtime", async ({
    page,
  }) => {
    await page.goto("/controller");

    const sceneDebug = await page.evaluate(() => window.getSceneDebug());
    expect(sceneDebug.hasWindowRenderer).toBe(true);
    expect(sceneDebug.hasPneumaticTube).toBe(true);
    expect(sceneDebug.hasPacketCourier).toBe(true);
    expect(sceneDebug.hasOwlCourier).toBe(true);
    expect(sceneDebug.hasAudio8).toBe(true);
    expect(sceneDebug.tube.x).toBe(988);
    expect(sceneDebug.characterSkins.Codex).toContain("프리렌");
    expect(sceneDebug.characterSkins.Claude).toContain("아카네");
    expect(sceneDebug.characterSkins.Gemini).toContain("귀여운");

    const petResult = await page.evaluate(() => window.testPetCat());
    expect(petResult.catState).toBe("pet");
    expect(petResult.particleCount).toBeGreaterThan(0);
    expect(petResult.hasAudio8).toBe(true);
  });

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

  test("controller renders token HUD from monitor snapshot fallback", async ({ page }) => {
    await page.addInitScript(() => {
      window.__officeMonitorSocketDisabled = true;
    });
    const runtime = {
      runtime_state: "RUNNING",
      project_root: "/tmp/projectH",
      lanes: [
        { name: "Claude", state: "ready", note: "" },
        { name: "Codex", state: "working", note: "monitoring" },
        { name: "Gemini", state: "off", note: "" },
      ],
      control: { active_control_status: "implement", active_control_seq: 99 },
      watcher: { alive: true },
      active_round: { state: "ACTIVE" },
      artifacts: {},
    };
    await page.route("**/api/runtime/status", (route) =>
      route.fulfill({
        contentType: "application/json",
        body: JSON.stringify(runtime),
      }),
    );
    await page.route("**/api/runtime/monitor-snapshot", (route) =>
      route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          ok: true,
          runtime,
          hud: {
            collector: { phase: "idle" },
            totals: {
              total_tokens: 1500,
              total_cost_usd: 0.42,
              cache_hit_rate: 0.25,
            },
            agents: [
              {
                name: "Codex",
                state: "working",
                active: true,
                events: 7,
                total_tokens: 1500,
                total_cost_usd: 0.42,
                cache_hit_rate: 0.33,
              },
            ],
          },
          coordination_state: {
            Codex: {
              team_id: "round-99",
              parent_id: "prompt-root",
              approval_wait: true,
            },
          },
          teams: [
            {
              id: "round-99",
              label: "Round 99",
              agents: ["Claude", "Codex"],
              color: "#6aa7c9",
              source: "test",
            },
          ],
          communications: [
            {
              sequence: 1,
              from: "Claude",
              to: "Codex",
              event_type: "handoff",
              message: "delegate verification",
            },
          ],
        }),
      }),
    );

    await page.goto("/controller");

    await expect(page.locator("#tab-content")).toContainText("Token HUD");
    await expect(page.locator("#tab-content")).toContainText("fallback");
    await expect(page.locator("#tab-content")).toContainText("25%cache");
    const codexRow = page.locator('.token-agent-row[data-agent="Codex"]');
    await expect(codexRow).toContainText("WORKING");
    await expect(codexRow).toContainText("1.5k");
    await expect(codexRow).toContainText("$0.42");
    await expect(codexRow).toContainText("33%");
    await expect(page.locator("#event-list")).toContainText("Claude → Codex");
    await expect(page.locator("#event-list")).toContainText("Codex: 승인 대기");
    const sceneDebug = await page.evaluate(() => window.getSceneDebug());
    expect(sceneDebug.hasTeamHullRenderer).toBe(true);
    expect(sceneDebug.hasCommunicationTransfer).toBe(true);
    expect(sceneDebug.hasApprovalMarker).toBe(true);
    expect(sceneDebug.hasViewCulling).toBe(true);
    expect(sceneDebug.teamCount).toBe(1);
    expect(sceneDebug.communicationTransferCount).toBeGreaterThan(0);
    const positions = await page.evaluate(() => window.getAgentPositions());
    expect(positions.Codex.teamId).toBe("round-99");
    expect(positions.Codex.approvalWaiting).toBe(true);
  });

  test("controller deduplicates repeated status fetch failures and logs one recovery", async ({
    page,
  }) => {
    await disableRuntimeMonitor(page);
    let statusPollCount = 0;
    await page.route("**/api/runtime/status", async (route) => {
      statusPollCount += 1;
      if (statusPollCount <= 3) {
        await route.abort();
        return;
      }
      await route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          runtime_state: "RUNNING",
          project_root: "/tmp/projectH",
          lanes: [
            { name: "Claude", state: "working", note: "implementing slice" },
            { name: "Codex", state: "ready", note: "waiting for handoff" },
            { name: "Gemini", state: "off", note: "" },
          ],
          control: { active_control_status: "implement", active_control_seq: 77 },
          watcher: { alive: true },
          active_round: { state: "ACTIVE" },
          artifacts: {
            latest_work: { path: "work/4/19/demo-work.md", mtime: "2026-04-19T00:00:00Z" },
            latest_verify: { path: "verify/4/19/demo-verify.md", mtime: "2026-04-19T00:00:00Z" },
          },
        }),
      });
    });

    await page.goto("/controller");
    await page.waitForTimeout(2800);

    const failureMsgs = page
      .locator("#event-list .event-msg")
      .filter({ hasText: "상태 조회 실패: Failed to fetch" });
    await expect(failureMsgs).toHaveCount(1);

    const recoveryMsgs = page
      .locator("#event-list .event-msg")
      .filter({ hasText: "상태 조회 복구: Failed to fetch" });
    await expect(recoveryMsgs).toHaveCount(1);
    await expect(page.locator("#status-badge")).toHaveText("RUNNING");
  });

  test("controller surfaces automation attention detail from runtime status", async ({ page }) => {
    await disableRuntimeMonitor(page);
    await page.route("**/api/runtime/status", (route) =>
      route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          runtime_state: "RUNNING",
          project_root: "/tmp/projectH",
          automation_health: "attention",
          automation_reason_code: "stale_control_advisory",
          automation_incident_family: "stale_control_advisory",
          automation_next_action: "advisory_followup",
          automation_health_detail: "제어 슬롯 고착 감지됨 (900 사이클)",
          control_age_cycles: 900,
          stale_advisory_pending: true,
          lanes: [
            { name: "Claude", state: "ready", note: "waiting" },
            { name: "Codex", state: "ready", note: "waiting" },
            { name: "Gemini", state: "ready", note: "waiting" },
          ],
          control: { active_control_status: "implement", active_control_seq: 88 },
          watcher: { alive: true },
          active_round: { state: "IDLE" },
          artifacts: {
            latest_work: { path: "work/4/19/demo-work.md", mtime: "2026-04-19T00:00:00Z" },
            latest_verify: { path: "verify/4/19/demo-verify.md", mtime: "2026-04-19T00:00:00Z" },
          },
        }),
      }),
    );

    await page.goto("/controller");
    await page.waitForTimeout(700);

    await expect(page.locator("#status-badge")).toHaveText("RUNNING");
    const incidentRoom = page.locator("#tab-content").filter({ hasText: "Incident Room" });
    await expect(incidentRoom).toContainText("attention");
    await expect(incidentRoom).toContainText("stale_control_advisory");
    await expect(incidentRoom).toContainText("stale_advisory_pending");
  });

  test("controller renders main operator attention board for needs_operator reason", async ({ page }) => {
    await disableRuntimeMonitor(page);
    await page.route("**/api/runtime/status", (route) =>
      route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          runtime_state: "RUNNING",
          project_root: "/tmp/projectH",
          automation_health: "needs_operator",
          automation_reason_code: "claude_auth_login_required",
          automation_next_action: "operator_required",
          automation_health_detail: "lane tail에서 Please run /login 감지",
          degraded_reason: "claude_auth_login_required",
          degraded_reasons: ["claude_auth_login_required"],
          role_owners: { implement: "Claude", verify: "Codex", advisory: "Gemini" },
          lanes: [
            { name: "Claude", state: "broken", note: "auth_login_required", pid: 101 },
            { name: "Codex", state: "ready", note: "waiting" },
            { name: "Gemini", state: "ready", note: "waiting" },
          ],
          control: {
            active_control_file: ".pipeline/operator_request.md",
            active_control_status: "needs_operator",
            active_control_seq: 123,
          },
          autonomy: {
            mode: "needs_operator",
            reason_code: "claude_auth_login_required",
            decision_required: "Claude lane에서 /login을 완료하세요.",
            operator_policy: "immediate_publish",
            operator_eligible: true,
          },
          turn_state: { state: "CLAUDE_ACTIVE", active_role: "implement", active_lane: "Claude" },
          watcher: { alive: true },
          active_round: { state: "CLAUDE_ACTIVE" },
          artifacts: {},
        }),
      }),
    );
    await page.route("**/api/runtime/capture-tail**", (route) =>
      route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({ ok: true, text: "Please run /login" }),
      }),
    );

    await page.goto("/controller");
    const board = page.locator("#operator-attention-board");
    await expect(board).toBeVisible();
    await expect(board).toContainText("개입 필요");
    await expect(board).toContainText("인증 로그인 필요");
    await expect(board).toContainText("claude_auth_login_required");
    await expect(board).toContainText("Claude / IMPLEMENT");
    await expect(board).toContainText("Claude lane에서 /login을 완료하세요.");
    await expect(board).toContainText("operator_request.md · #123");
    await expect(board).toContainText("lane tail에서 Please run /login 감지");

    const attention = await page.evaluate(() => window.getOperatorAttentionDebug());
    expect(attention.tone).toBe("auth");
    expect(attention.laneName).toBe("Claude");

    await page.locator("#operator-attention-open-log").click();
    await expect(page.locator("#log-modal")).toHaveClass(/open/);
    await expect(page.locator("#lm-name")).toHaveText("Claude");
  });

  test("controller shows active verify owner as working even when lane snapshot is ready", async ({
    page,
  }) => {
    await disableRuntimeMonitor(page);
    await page.route("**/api/runtime/status", (route) =>
      route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          runtime_state: "RUNNING",
          project_root: "/tmp/projectH",
          role_owners: { implement: "Codex", verify: "Claude", advisory: "Gemini" },
          lanes: [
            { name: "Claude", state: "ready", note: "prompt visible" },
            { name: "Codex", state: "ready", note: "waiting" },
            { name: "Gemini", state: "ready", note: "waiting" },
          ],
          control: { active_control_status: "none", active_control_seq: -1 },
          watcher: { alive: true },
          active_round: { job_id: "verify-1", state: "VERIFYING" },
          turn_state: { state: "IDLE", active_role: "", active_lane: "" },
          artifacts: {
            latest_work: { path: "work/4/23/demo-work.md", mtime: "2026-04-23T00:00:00Z" },
            latest_verify: { path: "verify/4/23/demo-verify.md", mtime: "2026-04-23T00:00:00Z" },
          },
        }),
      }),
    );
    await page.route("**/api/runtime/capture-tail**", (route) =>
      route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({ ok: true, text: "verification running" }),
      }),
    );
    await page.route("**/api/runtime/agent-inspector**", (route) =>
      route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          ok: true,
          agent: { id: "Claude", role: "verify", state: "working", note: "prompt visible", pid: 123 },
          metrics: { total_tokens: 1200, total_cost_usd: 0.08, cache_hit_rate: 0.5 },
          current_prompt: "Prompt: verify controller monitor",
          conversation: ["User: inspect this", "Assistant: verification running"],
        }),
      }),
    );

    await page.goto("/controller");
    await page.waitForFunction(() => window.getAgentPositions?.()?.Claude?.state === "working");

    const positions = await page.evaluate(() => window.getAgentPositions());
    expect(positions.Claude.state).toBe("working");
    expect(positions.Codex.state).toBe("ready");
    await expect(page.locator("#tab-content")).toContainText("VERIFYING");

    await page.locator('.agent-card[data-agent="Claude"]').click();
    await expect(page.locator("#agent-inspector")).toHaveClass(/open/);
    await expect(page.locator("#agent-inspector")).toContainText("Prompt: verify controller monitor");
    await expect(page.locator("#agent-inspector")).toContainText("50%");
    await page.locator("#ai-open-log").click();
    await expect(page.locator("#lm-state")).toHaveText("WORKING");
  });

  test("marquee text keeps moving when the polled runtime payload is unchanged", async ({
    page,
  }) => {
    await disableRuntimeMonitor(page);
    await page.route("**/api/runtime/status", (route) =>
      route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          runtime_state: "RUNNING",
          project_root: "/tmp/projectH",
          lanes: [
            { name: "Claude", state: "working", note: "implementing slice" },
            { name: "Codex", state: "ready", note: "waiting for handoff" },
            { name: "Gemini", state: "off", note: "" },
          ],
          control: { active_control_status: "implement", active_control_seq: 42 },
          watcher: { alive: true },
          active_round: { state: "ACTIVE" },
          artifacts: {
            latest_work: { path: "work/4/18/demo-work.md", mtime: "2026-04-18T00:00:00Z" },
            latest_verify: { path: "verify/4/18/demo-verify.md", mtime: "2026-04-18T00:00:00Z" },
          },
        }),
      }),
    );

    await page.goto("/controller");

    const marquee = page.locator("#marquee-text");
    await expect(marquee).toContainText("Runtime RUNNING");

    const readTranslateX = () =>
      page.evaluate(() => {
        const el = document.getElementById("marquee-text");
        if (!el) return 0;
        const transform = getComputedStyle(el).transform;
        if (!transform || transform === "none") return 0;
        const match = transform.match(/matrix(3d)?\((.+)\)/);
        if (!match) return 0;
        const parts = match[2].split(",").map((value) => Number(value.trim()));
        return match[1] ? (parts[12] || 0) : (parts[4] || 0);
      });

    const x1 = await readTranslateX();
    await page.waitForTimeout(2500);
    const x2 = await readTranslateX();
    await page.waitForTimeout(2500);
    const x3 = await readTranslateX();

    expect(x2).toBeLessThan(x1 - 20);
    expect(x3).toBeLessThan(x2 - 20);
  });

  test("agent cards expose data-fatigue attribute for fatigue observability", async ({
    page,
  }) => {
    await disableRuntimeMonitor(page);
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
    await disableRuntimeMonitor(page);
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
    await disableRuntimeMonitor(page);
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

  test("idle agents settle into lounge rest bounds", async ({
    page,
  }) => {
    await disableRuntimeMonitor(page);
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

    // Read lounge rest-zone map from the controller
    const bounds = await page.evaluate(() => window.getRoamBounds());
    const zone = bounds.restZones.Claude;
    expect(zone).toBeTruthy();

    const position = await page.evaluate(() => window.getAgentPositions().Claude);
    expect(position.atLounge).toBe(true);
    expect(position.x).toBeGreaterThanOrEqual(zone.x);
    expect(position.x).toBeLessThanOrEqual(zone.x + zone.w);
    expect(position.y).toBeGreaterThanOrEqual(zone.y);
    expect(position.y).toBeLessThanOrEqual(zone.y + zone.h);

    // Force 30 idle roam picks and collect the coordinates
    const points = await page.evaluate(() => window.testPickIdleTargets("Claude", 30));
    expect(points.length).toBe(30);

    for (const pt of points) {
      // Must be within the agent's lounge rest zone
      expect(pt.x).toBeGreaterThanOrEqual(zone.x);
      expect(pt.x).toBeLessThanOrEqual(zone.x + zone.w);
      expect(pt.y).toBeGreaterThanOrEqual(zone.y);
      expect(pt.y).toBeLessThanOrEqual(zone.y + zone.h);
    }
  });

  test("lounge rest zones keep idle agents partitioned", async ({
    page,
  }) => {
    await disableRuntimeMonitor(page);
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

    // Idle agents rest inside their own lounge seat partition, so even with
    // a phantom placed elsewhere the sampled points should stay in Claude's
    // assigned lounge rest zone.
    const bounds = await page.evaluate(() => window.getRoamBounds());
    const zone = bounds.restZones.Claude;

    // Place phantom outside Claude's zone (e.g. center of Codex desk)
    const codexZone = bounds.zones.codex_desk;
    const cx = codexZone.x + codexZone.w / 2;
    const cy = codexZone.y + codexZone.h / 2;

    const results = await page.evaluate(
      ({ cx, cy }) => window.testAntiStacking("Claude", cx, cy, 50),
      { cx, cy },
    );
    expect(results.length).toBe(50);

    // All picks should still be within Claude's lounge rest zone
    for (const r of results) {
      expect(r.x).toBeGreaterThanOrEqual(zone.x);
      expect(r.x).toBeLessThanOrEqual(zone.x + zone.w);
      expect(r.y).toBeGreaterThanOrEqual(zone.y);
      expect(r.y).toBeLessThanOrEqual(zone.y + zone.h);
    }
  });

  test("lounge idle roam uses continuous micro-roam (no spot history)", async ({
    page,
  }) => {
    await disableRuntimeMonitor(page);
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

    // Lounge resting uses continuous micro-roam within the assigned seat zone
    // instead of discrete spot-based movement. testHistoryPenalty returns
    // an empty array because the spot history concept no longer applies.
    const results = await page.evaluate(() =>
      window.testHistoryPenalty("Claude", [0, 1, 2, 3, 4], 120),
    );
    expect(results.length).toBe(0);

    // Verify that idle picks still produce valid lounge-rest coordinates
    const points = await page.evaluate(() => window.testPickIdleTargets("Claude", 20));
    expect(points.length).toBe(20);
    const bounds = await page.evaluate(() => window.getRoamBounds());
    const zone = bounds.restZones.Claude;
    for (const pt of points) {
      expect(pt.x).toBeGreaterThanOrEqual(zone.x);
      expect(pt.x).toBeLessThanOrEqual(zone.x + zone.w);
      expect(pt.y).toBeGreaterThanOrEqual(zone.y);
      expect(pt.y).toBeLessThanOrEqual(zone.y + zone.h);
    }
  });
});
