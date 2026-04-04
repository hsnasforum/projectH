# review-queue-item-statement exact-text smoke tightening

날짜: 2026-04-04
슬라이스: review-queue-item-statement exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 first visible review queue rendering의 item statement assertion을 box-level `toContainText`에서 dedicated `[data-testid="review-queue-item"]` 내 `<strong>` element exact-text `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:638` — `reviewQueueBox.getByTestId("review-queue-item").locator("strong").first()` 기준 `toHaveText("explicit rewrite correction recorded for this grounded brief")` 1건으로 교체

## 변경 내용

- 기존 line 638의 `await expect(reviewQueueBox).toContainText("explicit rewrite correction recorded for this grounded brief")`를 dedicated title element 기준 exact-text assertion으로 교체했습니다.
- 런타임 `app/static/app.js:2447-2449`에서 `<strong>` element에 `item.statement`를 직접 렌더링하며, `[data-testid="review-queue-item"]`(line 2440)이 card에 설정됩니다.
- aggregate trigger title(line 744)과 동일한 selector 패턴입니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n 'explicit rewrite correction recorded for this grounded brief|review-queue-item' e2e/tests/web-smoke.spec.mjs app/static/app.js`: test 1건 + runtime 1건 확인
- `make e2e-test`: 17 passed (2.4m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. review queue item statement exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- review queue item 내부의 meta basis/status assertions(line 639-640)는 아직 box-level `toContainText`로 남아 있습니다. meta span에 dynamic timestamp(`업데이트 ...`)가 포함되어 있어 exact-text보다 scoped selector가 필요합니다.

## 커밋

- `733f647` test: tighten review-queue-item-statement to exact-text on dedicated element
