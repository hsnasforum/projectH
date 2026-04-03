# aggregate-transition initial-unblocked helper exact-text smoke tightening

날짜: 2026-04-04
슬라이스: aggregate-transition initial-unblocked helper exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 aggregate initial-unblocked helper assertion을 box-level partial match에서 dedicated helper testid level exact-text match로 강화합니다. 이것은 aggregate helper exact-text smoke tightening 시리즈의 마지막 슬라이스입니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:747` — `aggregateTriggerBox.toContainText(...)` → `aggregateTriggerBox.getByTestId("aggregate-trigger-helper").toHaveText("검토 메모 적용을 시작할 수 있습니다. 사유를 입력한 뒤 시작 버튼을 누르세요.")`

## 변경 내용

- 기존 box-level `toContainText`를 dedicated `aggregate-trigger-helper` testid에 대한 `toHaveText` exact match로 교체했습니다.
- 런타임 `app/static/app.js:1326-1327`의 `aggregateTriggerBlockedHelper()` unblocked branch 전체 문자열과 정확히 일치합니다.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `make e2e-test`: 17 passed (2.6m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. helper exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- 이 슬라이스로 aggregate helper exact-text family 전체가 완료되었습니다 (initial-unblocked, emitted, applied-pending, result, stopped, reversed, conflict — 총 7건).
- 금일 전체 smoke tightening 시리즈: notice 17건 + status-label 4건 + helper 7건 = 총 28개 assertion 강화 완료.

## 커밋

- `eac9db4` test: tighten aggregate-transition initial-unblocked helper to exact-text on dedicated testid
