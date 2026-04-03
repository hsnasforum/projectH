# aggregate-transition result helper exact-text smoke tightening

날짜: 2026-04-04
슬라이스: aggregate-transition result helper exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 aggregate result helper assertion을 box-level partial match에서 dedicated helper testid level exact-text match로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:815` — `aggregateTriggerBox.toContainText("검토 메모 적용 효과가 활성화되었습니다.")` → `aggregateTriggerBox.getByTestId("aggregate-trigger-helper").toHaveText("검토 메모 적용 효과가 활성화되었습니다. 이후 응답에 교정 패턴이 반영됩니다.")`

## 변경 내용

- 기존 box-level `toContainText`는 메시지 전반부만 매칭했으나, dedicated `aggregate-trigger-helper` testid에 대해 런타임 `app/static/app.js:2597`의 `hasAppliedResult` branch 전체 문자열 `"검토 메모 적용 효과가 활성화되었습니다. 이후 응답에 교정 패턴이 반영됩니다."`로 exact match합니다.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg` 교차 확인: runtime helper text와 smoke expected value 일치
- `make e2e-test`: 1차 unrelated intermittent failure (test 12 line 741), 2차 17 passed (2.3m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. helper exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- stopped/reversed/conflict-checked helper assertions는 이번 라운드 범위 밖.

## 커밋

- `9d8b8cb` test: tighten aggregate-transition result helper to exact-text on dedicated testid
