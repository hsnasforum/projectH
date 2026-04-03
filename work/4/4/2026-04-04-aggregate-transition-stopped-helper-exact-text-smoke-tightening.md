# aggregate-transition stopped helper exact-text smoke tightening

날짜: 2026-04-04
슬라이스: aggregate-transition stopped helper exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 aggregate stopped helper assertion을 box-level partial match에서 dedicated helper testid level exact-text match로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:829` — `aggregateTriggerBox.toContainText(...)` → `aggregateTriggerBox.getByTestId("aggregate-trigger-helper").toHaveText("검토 메모 적용이 중단되었습니다. 이후 응답에 교정 패턴이 반영되지 않습니다.")`

## 변경 내용

- 기존 box-level `toContainText`를 dedicated `aggregate-trigger-helper` testid에 대한 `toHaveText` exact match로 교체했습니다.
- 런타임 `app/static/app.js:2594-2595`의 `hasStopped` branch 전체 문자열과 정확히 일치합니다.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `make e2e-test`: 17 passed (2.3m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. helper exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- reversed/conflict-checked helper assertions는 이번 라운드 범위 밖.

## 커밋

- `57b97b3` test: tighten aggregate-transition stopped helper to exact-text on dedicated testid
