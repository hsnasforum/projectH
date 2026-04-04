# review-queue-basis-meta scoped-selector smoke tightening

날짜: 2026-04-04
슬라이스: review-queue-basis-meta scoped-selector smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 first visible review queue rendering의 basis meta assertion을 box-level `toContainText`에서 dedicated meta span selector-scoped `toContainText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:639` — `reviewQueueBox.getByTestId("review-queue-item").locator(".history-item-title span")` 기준 scoped `toContainText("기준 명시 확인")` 1건으로 교체

## 변경 내용

- 기존 line 639의 `await expect(reviewQueueBox).toContainText("기준 명시 확인")`를 dedicated meta span selector 기준 scoped assertion으로 교체했습니다.
- meta span은 런타임 `app/static/app.js:2451-2456`에서 `기준 ... · 상태 ... · 업데이트 ...`를 동적으로 합치므로, full exact-text가 아닌 scoped `toContainText`로 검증합니다.
- aggregate trigger capability/audit meta(line 745-746)와 동일한 selector 패턴입니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n '기준 명시 확인|review-queue-item|history-item-title|업데이트' e2e/tests/web-smoke.spec.mjs app/static/app.js`: test + runtime 다수 확인
- `make e2e-test`: 17 passed (2.4m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. basis meta scoped-selector 강화만 수행했으며 런타임 behavior 변경 없음.
- 같은 meta span의 `상태 검토 대기`(line 640)도 동일한 패턴으로 좁힐 수 있으나 이번 슬라이스 범위 밖입니다.

## 커밋

- `bcd69c6` test: tighten review-queue-basis-meta to scoped selector on meta span
