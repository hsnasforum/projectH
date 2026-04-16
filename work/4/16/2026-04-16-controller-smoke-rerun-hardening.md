# 2026-04-16 controller smoke rerun hardening

## 변경 파일
- `e2e/playwright.controller.config.mjs`
- `Makefile`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음

## 변경 이유
- 이전 verification 라운드에서 controller smoke 재실행 시 `Address already in use` 노이즈가 발생할 수 있음을 확인했습니다. `e2e/playwright.controller.config.mjs`가 포트 `8781`을 하드코딩하고 `reuseExistingServer: false`를 사용하기 때문입니다.
- 이번 슬라이스는 포트를 `CONTROLLER_SMOKE_PORT` 환경 변수로 설정 가능하게 하고, `make controller-test` 진입점을 추가하여 controller smoke 재실행 ergonomics를 개선합니다.

## 핵심 변경
- `e2e/playwright.controller.config.mjs`
  - `process.env.CONTROLLER_SMOKE_PORT || "8781"`로 포트를 읽어 `use.baseURL`, `webServer.command`, `webServer.url` 세 곳에 동일하게 반영
  - 기본값 `8781`은 변경 없음
- `Makefile`
  - `controller-test` target 추가: `cd e2e && npx playwright test -c playwright.controller.config.mjs --reporter=line`
  - `.PHONY`에 `controller-test` 추가
  - `e2e-test`에는 포함하지 않음 (controller는 `app.web` release gate 밖)
- root docs 4건: controller smoke 설명에 `make controller-test` 진입점과 `CONTROLLER_SMOKE_PORT` 포트 오버라이드 반영

## 검증
- `make controller-test`
  - 결과: `2 passed (3.0s)`
- `CONTROLLER_SMOKE_PORT=8782 make controller-test`
  - 결과: `2 passed (2.9s)`
- `git diff --check -- e2e/playwright.controller.config.mjs Makefile README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: 출력 없음 (whitespace 문제 없음)
- `make e2e-test` full browser suite 생략. 이번 변경은 controller-only config/Makefile/docs이며 `app.web` 시나리오에 영향 없음.

## 남은 리스크
- 동일 포트에서 동시에 두 개의 controller smoke를 실행하면 여전히 충돌합니다. `CONTROLLER_SMOKE_PORT` 오버라이드로 포트를 분리하면 회피 가능합니다.
- controller smoke는 여전히 `app.web` release gate 밖 별도 실행입니다.
