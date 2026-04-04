# aggregate-trigger-audit-meta scoped-selector smoke tightening

날짜: 2026-04-04
슬라이스: aggregate-trigger-audit-meta scoped-selector smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 same-session recurrence aggregate scenario의 `audit contract_only_not_emitted` assertion을 box-level `toContainText`에서 meta span selector-scoped `toContainText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:746` — `aggregate-trigger-item` 내 `.history-item-title span` 기준 scoped `toContainText("audit contract_only_not_emitted")` 1건으로 교체

## 변경 내용

- 기존 line 746의 `await expect(aggregateTriggerBox).toContainText("audit contract_only_not_emitted")`를 `await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-item").locator(".history-item-title span")).toContainText("audit contract_only_not_emitted")`로 교체했습니다.
- 이전 capability 슬라이스와 동일한 meta span selector 패턴입니다. 런타임 `app/static/app.js:2547-2554`에서 동적 content와 함께 결합되므로 scoped `toContainText`를 사용합니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n 'audit contract_only_not_emitted|history-item-title|capabilityOutcome|auditStage' e2e/tests/web-smoke.spec.mjs app/static/app.js`: test 2건(capability + audit) + runtime 다수 확인
- `make e2e-test`: 17 passed (2.3m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. audit meta selector-scoped 강화만 수행했으며 런타임 behavior 변경 없음.
- same-session recurrence aggregate scenario의 unblocked branch visible 직후 assertions는 이제 모두 dedicated element 또는 scoped selector 기준으로 검증됩니다 (status, section-label, title, capability, audit, planning-target, helper).

## 커밋

- `aeaeb58` test: tighten aggregate-trigger-audit-meta to scoped selector on meta span
