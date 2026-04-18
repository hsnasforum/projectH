# 2026-04-18 README controller smoke inventory truth-sync

## 변경 파일
- `README.md`

## 사용 skill
- `superpowers:using-superpowers`
- `doc-sync`

## 변경 이유
- `verify/4/18/2026-04-18-controller-cozy-assets-runtime-sync-verification.md`가 shared `cozy.js` ownership restore와 zone-bounded roam 문서 sync는 대체로 맞지만 `README.md`의 `Current controller smoke scenarios` 블록이 아직 예전 8개 시나리오(walkable-bounds / desk exclusion rect / proximity anti-stacking / `_roamHistory` penalty)를 적고 있고, 실제 `e2e/tests/controller-smoke.spec.mjs`에 있는 `cozy runtime loads from shared /controller-assets/js/cozy.js module`과 `marquee text keeps moving when the polled runtime payload is unchanged` 시나리오를 누락하고 있다고 기록했습니다.
- `.pipeline/claude_handoff.md` `STATUS: implement`(`CONTROL_SEQ: 292`)는 이 한 덩어리의 docs-only drift만 좁게 닫으라고 지시했고, `controller/index.html`, `controller/js/*.js`, `controller/css/office.css`, `e2e/tests/controller-smoke.spec.mjs`, 다른 문서는 건드리지 말라고 scope를 잠갔습니다.

## 핵심 변경
- `README.md`의 `### Controller Smoke (separate from app.web)` 아래 smoke inventory를 실제 10개 시나리오로 다시 적었습니다. source of truth는 `e2e/tests/controller-smoke.spec.mjs`, `e2e/playwright.controller.config.mjs`, `Makefile` 입니다.
- 새 inventory는 spec 파일의 실제 실행 순서와 번호를 맞춰 정리했습니다.
  1. `cozy runtime loads from shared /controller-assets/js/cozy.js module` — `<script src="/controller-assets/js/cozy.js">` 태그가 정확히 하나이고 `window.getRoamBounds`, `window.setAgentFatigue`, `window.testPickIdleTargets`, `window.testAntiStacking`, `window.testHistoryPenalty`가 모두 function으로 reachable함을 assert.
  2. storage blocked일 때 `#storage-warn` 칩 + 1회 event log 경고.
  3. storage available일 때 `#storage-warn` 숨김 + event log 경고 없음.
  4. `marquee text keeps moving when the polled runtime payload is unchanged` — 동일 payload로 `/api/runtime/status`를 stub해도 `#marquee-text` translateX가 2.5s 두 샘플에서 monotonically 감소하도록 assert.
  5. `data-fatigue` 속성 observability.
  6. `setAgentFatigue` hook `fatigued` 전이(`💦 피로 누적`).
  7. `setAgentFatigue` hook `coffee` 전이(`☕ 커피 충전 중`).
  8. idle roam target이 home desk zone (`claude_desk`) 안에 머무름 — `testPickIdleTargets("Claude", 30)` 결과 30개 모두 zone rect 안.
  9. zone-bounded agents inherently avoid stacking — phantom을 `codex_desk` 중앙에 두고 `testAntiStacking("Claude", cx, cy, 50)` 50개 모두 여전히 `claude_desk` 안, 즉 `testAntiStacking`이 zone isolation 덕분에 `testPickIdleTargets`에 위임.
  10. zone-bounded idle roam uses continuous micro-roam (no spot history) — `testHistoryPenalty("Claude", [0,1,2,3,4], 120)`가 빈 배열을 반환, 동시에 `testPickIdleTargets("Claude", 20)`가 20개 모두 `claude_desk` 안에 있도록 assert.
- run instruction도 handoff가 지시한 dedicated controller smoke path로 다시 정리했습니다. `make controller-test`를 기본으로 두고 동일 기능의 직접 호출(`cd e2e && CONTROLLER_SMOKE_PORT=<free-port> npx playwright test -c playwright.controller.config.mjs --reporter=line`)과 port override(`CONTROLLER_SMOKE_PORT=8782 make controller-test`)를 같이 적었습니다.
- controller runtime code, test 코드, 다른 문서는 건드리지 않았습니다. `controller/index.html`, `controller/js/*.js`, `controller/css/office.css`, `e2e/tests/controller-smoke.spec.mjs`, `tests/test_controller_server.py`, `docs/*`는 이번 라운드 diff에 포함되지 않습니다.

## 검증
- `git diff --check -- README.md`
  - 결과: 통과
- 이번 슬라이스는 docs-only truth-sync이므로 browser rerun은 수행하지 않았습니다. README 문장은 `e2e/tests/controller-smoke.spec.mjs`의 실제 10개 `test(...)` 선언, `e2e/playwright.controller.config.mjs`의 `python3 -m controller.server` / 기본 port 8781 / `CONTROLLER_SMOKE_PORT` 오버라이드 정의, `Makefile`의 `controller-test: cd e2e && npx playwright test -c playwright.controller.config.mjs --reporter=line` 타겟을 source of truth로 맞췄습니다.
- latest verify 환경(`verify/4/18/2026-04-18-controller-cozy-assets-runtime-sync-verification.md`)에서 `make controller-test` / dedicated command 모두 `python3 -m controller.server` bind 단계에서 `PermissionError: [Errno 1] Operation not permitted`로 막혔다는 사실이 이미 기록돼 있으므로, 이번 라운드에서 smoke pass를 새로 주장하지 않았습니다.

## 남은 리스크
- `controller/js/cozy.js` 단일 대형 모듈과 기존 orphan `controller/js/{state,sidebar,panel,audio,agents,config}.js` 정리는 여전히 남아 있습니다. 이번 docs-only 슬라이스에서는 의도적으로 reopen하지 않았습니다.
- controller smoke의 실제 bind 가능 여부는 verify sandbox에서 계속 환경 제약을 받을 수 있습니다. 이후 `/work`에서 smoke pass를 다시 주장할 때는 dedicated controller command로 맞추고 bind 가능 환경인지 여부를 같이 명시하는 편이 맞습니다.
