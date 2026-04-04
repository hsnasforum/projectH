# review-queue-status-meta scoped-selector smoke tightening

날짜: 2026-04-04
슬라이스: review-queue-status-meta scoped-selector smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 first visible review queue rendering의 status meta assertion을 box-level `toContainText`에서 dedicated meta span selector-scoped `toContainText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:640` — `reviewQueueBox.getByTestId("review-queue-item").locator(".history-item-title span")` 기준 scoped `toContainText("상태 검토 대기")` 1건으로 교체

## 변경 내용

- 기존 line 640의 `await expect(reviewQueueBox).toContainText("상태 검토 대기")`를 dedicated meta span selector 기준 scoped assertion으로 교체했습니다.
- 이전 basis 슬라이스(line 639)와 동일한 selector 패턴입니다. meta span에 dynamic `업데이트 ...`가 포함되어 있어 scoped `toContainText`를 사용합니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n '상태 검토 대기|review-queue-item|history-item-title' e2e/tests/web-smoke.spec.mjs app/static/app.js`: test + runtime 다수 확인
- `make e2e-test`: 17 passed (2.5m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. status meta scoped-selector 강화만 수행했으며 런타임 behavior 변경 없음.
- first visible review queue rendering의 모든 visible assertions(section-label, status-hint, item-statement, basis-meta, status-meta, accept-button)가 이제 dedicated element 또는 scoped selector 기준으로 검증됩니다.

## 커밋

- `7ed58e2` test: tighten review-queue-status-meta to scoped selector on meta span
