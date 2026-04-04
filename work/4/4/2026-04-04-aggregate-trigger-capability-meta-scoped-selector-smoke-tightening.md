# aggregate-trigger-capability-meta scoped-selector smoke tightening

날짜: 2026-04-04
슬라이스: aggregate-trigger-capability-meta scoped-selector smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 same-session recurrence aggregate scenario의 `capability unblocked_all_required` assertion을 box-level `toContainText`에서 meta span selector-scoped `toContainText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:745` — `aggregate-trigger-item` 내 `.history-item-title span` 기준 scoped `toContainText("capability unblocked_all_required")` 1건으로 교체

## 변경 내용

- 기존 line 745의 `await expect(aggregateTriggerBox).toContainText("capability unblocked_all_required")`를 `await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-item").locator(".history-item-title span")).toContainText("capability unblocked_all_required")`로 교체했습니다.
- meta span은 런타임 `app/static/app.js:2547-2554`에서 `반복 N회 · 마지막 확인 ... · capability ... · audit ...`를 동적으로 합치므로, full exact-text가 아닌 scoped `toContainText`로 검증합니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n 'capability unblocked_all_required|history-item-title|capabilityOutcome|auditStage' e2e/tests/web-smoke.spec.mjs app/static/app.js`: test 1건 + runtime 다수 확인
- `make e2e-test`: 17 passed (2.3m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. capability meta selector-scoped 강화만 수행했으며 런타임 behavior 변경 없음.
- 같은 meta span 안의 `audit contract_only_not_emitted` assertion도 동일한 패턴으로 좁힐 수 있으나 이번 슬라이스 범위 밖입니다.

## 커밋

- `a4fa773` test: tighten aggregate-trigger-capability-meta to scoped selector on meta span
