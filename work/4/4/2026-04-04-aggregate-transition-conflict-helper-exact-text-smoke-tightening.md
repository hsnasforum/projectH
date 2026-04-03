# aggregate-transition conflict helper exact-text smoke tightening

날짜: 2026-04-04
슬라이스: aggregate-transition conflict helper exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 aggregate conflict helper assertion을 box-level partial match에서 dedicated helper testid level exact-text match로 강화합니다. 이것은 aggregate helper family smoke tightening 시리즈의 마지막 슬라이스입니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:870` — `aggregateTriggerBox.toContainText(...)` → `aggregateTriggerBox.getByTestId("aggregate-trigger-helper").toHaveText("충돌 확인이 완료되었습니다. 현재 aggregate 범위의 충돌 상태가 기록되었습니다.")`

## 변경 내용

- 기존 box-level `toContainText`를 dedicated `aggregate-trigger-helper` testid에 대한 `toHaveText` exact match로 교체했습니다.
- 런타임 `app/static/app.js:2590-2591`의 `hasReversed && conflictVisibilityRecord` branch 전체 문자열과 정확히 일치합니다.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `make e2e-test`: 17 passed (2.6m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. helper exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- 이 슬라이스로 aggregate helper family 전체 (result, stopped, reversed, conflict)가 완료되었습니다.
- aggregate smoke tightening 전체 시리즈 요약: notice family 17건 + status-label family 4건 + helper family 4건 = 총 25개 assertion이 강화되었습니다.

## 커밋

- `bfaef3e` test: tighten aggregate-transition conflict helper to exact-text on dedicated testid
