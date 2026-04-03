# aggregate-transition emitted helper exact-text smoke tightening

날짜: 2026-04-04
슬라이스: aggregate-transition emitted helper exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 aggregate emitted helper assertion을 dedicated helper testid level exact-text match로 추가합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:776` — `aggregateTriggerBox.getByTestId("aggregate-trigger-helper").toHaveText("transition record가 발행되었습니다. 적용 실행 버튼을 눌러 주세요.")` 추가

## 변경 내용

- emitted 상태에서 dedicated `aggregate-trigger-helper` testid에 대한 `toHaveText` exact match assertion 1건을 추가했습니다.
- 런타임 `app/static/app.js:2600-2601`의 `hasEmittedRecord` branch 전체 문자열 `"transition record가 발행되었습니다. 적용 실행 버튼을 눌러 주세요."`와 정확히 일치합니다.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `make e2e-test`: 1차 unrelated intermittent failure (test 8 line 397), 2차 17 passed (2.6m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. helper exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- applied-pending helper와 initial unblocked helper는 이번 라운드 범위 밖.

## 커밋

- `3e0cc22` test: tighten aggregate-transition emitted helper to exact-text on dedicated testid
