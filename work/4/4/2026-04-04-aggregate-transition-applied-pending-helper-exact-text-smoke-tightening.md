# aggregate-transition applied-pending helper exact-text smoke tightening

날짜: 2026-04-04
슬라이스: aggregate-transition applied-pending helper exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 aggregate applied-pending helper assertion을 dedicated helper testid level exact-text match로 추가합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:793` — `aggregateTriggerBox.getByTestId("aggregate-trigger-helper").toHaveText("검토 메모 적용이 실행되었습니다. 결과 확정 버튼을 눌러 주세요.")` 추가

## 변경 내용

- applied-pending 상태에서 dedicated `aggregate-trigger-helper` testid에 대한 `toHaveText` exact match assertion 1건을 추가했습니다.
- 런타임 `app/static/app.js:2598-2599`의 `hasAppliedPending` branch 전체 문자열과 정확히 일치합니다.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `make e2e-test`: 17 passed (2.7m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. helper exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- initial unblocked helper는 이번 라운드 범위 밖.

## 커밋

- `dc416d9` test: tighten aggregate-transition applied-pending helper to exact-text on dedicated testid
