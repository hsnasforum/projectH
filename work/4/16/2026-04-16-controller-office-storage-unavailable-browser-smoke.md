# 2026-04-16 controller office storage-unavailable browser smoke

## 변경 파일
- `controller/index.html`
- `e2e/playwright.controller.config.mjs` (신규)
- `e2e/tests/controller-smoke.spec.mjs` (신규)
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드에서 toolbar `#storage-warn` chip과 `PrefStore.available` 계약을 구현했지만, browser localStorage 차단 환경에서 실제로 chip이 표시되는지 real-browser 검증이 없었습니다.
- 이번 슬라이스는 Playwright init script로 `Storage.prototype` 메서드를 throw하도록 override하여 `PrefStore._probe()`가 실패하는 환경을 시뮬레이션하고, `#storage-warn` chip의 visibility/text/tooltip 계약을 browser에서 확인합니다.

## 핵심 변경
- `controller/index.html`
  - BOOT 섹션에서 `sw.style.display = ''` → `sw.style.display = 'inline-block'`으로 수정. CSS `.toolbar .storage-warn { display: none; }`이 기본이므로, `style.display = ''`로 inline style을 지우면 CSS fallback으로 다시 `none`이 되는 버그를 수정했습니다.
- `e2e/playwright.controller.config.mjs`
  - `python3 -m controller.server`를 port 8781에서 시작하는 dedicated controller Playwright config. `app.web` smoke와 분리.
  - `testMatch: "controller-smoke.spec.mjs"`로 controller 시나리오만 실행.
- `e2e/tests/controller-smoke.spec.mjs`
  - scenario 1: `Storage.prototype.setItem/getItem/removeItem`을 throw하도록 init script override → `#storage-warn` visible, text `⚠ 설정 비저장`, tooltip 확인.
  - scenario 2: 정상 localStorage 환경에서 `#storage-warn` hidden 확인.
- docs 4건: controller smoke 추가를 반영.

## 검증
- `cd e2e && npx playwright test -c playwright.controller.config.mjs --reporter=line`
  - 결과: `2 passed (3.3s)`
- `python3 -m unittest -v tests.test_controller_server.ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only`
  - 결과: `Ran 1 test in 0.002s`, `OK`
- `git diff --check -- controller/index.html e2e/playwright.controller.config.mjs e2e/tests/controller-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: 출력 없음 (whitespace 문제 없음)
- `make e2e-test` full browser suite는 생략. 이번 변경은 controller-only config와 controller HTML 버그 수정이며, `app.web` 시나리오에 영향 없음.

## 남은 리스크
- `sw.style.display = ''` 버그가 이전 라운드에서 감지되지 않은 이유는 unit test가 토큰 존재만 확인하고 CSS computed style을 검증하지 않았기 때문입니다. 이번 browser smoke로 해당 계약이 보강됐습니다.
- controller smoke는 `app.web` release gate 밖이므로, `make e2e-test`에는 포함되지 않습니다. 별도 실행 필요: `cd e2e && npx playwright test -c playwright.controller.config.mjs`.
- event log의 일회성 storage 경고(`환경 설정 저장 불가`) 표시는 이번 smoke에서 검증하지 않았습니다. 스크롤 위치와 타이밍에 의존하므로 별도 시나리오로 분리하는 편이 적절합니다.
