# 2026-04-16 controller office storage event-log warning smoke

## 변경 파일
- `e2e/tests/controller-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드에서 `#storage-warn` toolbar chip의 browser smoke를 추가했지만, event log에 표시되는 일회성 저장 불가 경고(`환경 설정 저장 불가 — 새로고침 시 toolbar 설정이 초기화됩니다`)는 browser 검증 대상에 포함되지 않았습니다.
- 이번 슬라이스는 기존 blocked-storage 시나리오에 event-log 경고 assertion을 추가하고, normal-storage 시나리오에 negative assertion을 추가하여 blocked-storage 진단 경로의 browser 검증을 완결합니다.

## 핵심 변경
- `e2e/tests/controller-smoke.spec.mjs`
  - blocked-storage 시나리오: `#event-list .event-msg` 중 경고 텍스트(`환경 설정 저장 불가 — 새로고침 시 toolbar 설정이 초기화됩니다`)가 정확히 1건 존재하는지 assertion 추가
  - normal-storage 시나리오: 같은 경고 텍스트가 0건인지 negative assertion 추가
  - 새 selector 없이 기존 `#event-list .event-msg` surface만 사용
- docs 4건: controller smoke 시나리오 설명에 event-log 경고 계약 반영

## 검증
- `cd e2e && npx playwright test -c playwright.controller.config.mjs -g "controller shows storage unavailable indicator when browser storage is blocked" --reporter=line`
  - 결과: `1 passed (2.3s)`
- `cd e2e && npx playwright test -c playwright.controller.config.mjs -g "controller hides storage indicator when browser storage is available" --reporter=line`
  - 결과: `1 passed (2.2s)`
- `git diff --check -- e2e/tests/controller-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: 출력 없음 (whitespace 문제 없음)
- `controller/index.html` 변경 없으므로 `test_controller_html_polls_runtime_api_only` 재실행 불필요
- `make e2e-test` full browser suite 생략. 이번 변경은 controller-only smoke assertion 추가이며 `app.web` 시나리오에 영향 없음.

## 남은 리스크
- `PrefStore._probe()`의 `pushEvent` 호출이 `_eventLogReady = true` 설정(line 1737) 이전에 실행되지만, `pushEvent`는 `_eventLogReady`를 확인하지 않으므로 DOM이 먼저 존재하면 정상 렌더링됩니다. 현재 inline script 위치상 문제 없으나, script 로딩 순서가 바뀌면 타이밍 이슈 가능성이 있습니다.
- controller smoke는 `app.web` release gate 밖이므로, 별도 실행 필요: `cd e2e && npx playwright test -c playwright.controller.config.mjs`.
