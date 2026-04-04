# aggregate-trigger-planning-target exact-text smoke tightening

날짜: 2026-04-04
슬라이스: aggregate-trigger-planning-target exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 same-session recurrence aggregate scenario의 planning-target assertion을 box-level `toContainText`에서 dedicated element exact-text `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:747` — `aggregate-trigger-item` 내 `.history-item-summary` 중 `계획 타깃` 필터 기준 `toHaveText("계획 타깃 eligible_for_reviewed_memory_draft_planning_only")` 1건으로 교체

## 변경 내용

- 기존 line 747의 `await expect(aggregateTriggerBox).toContainText("계획 타깃 eligible_for_reviewed_memory_draft_planning_only")`를 `await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-item").locator(".history-item-summary").filter({ hasText: "계획 타깃" })).toHaveText("계획 타깃 eligible_for_reviewed_memory_draft_planning_only")`로 교체했습니다.
- 런타임 `app/static/app.js:2566-2570`에서 planning-target은 별도 `div.history-item-summary`로 렌더링되며, identity summary `.history-item-summary`와 구분하기 위해 `filter({ hasText: "계획 타깃" })`를 사용합니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n '계획 타깃 eligible_for_reviewed_memory_draft_planning_only|planningTarget|history-item-summary' e2e/tests/web-smoke.spec.mjs app/static/app.js`: test 1건 + runtime 다수 확인
- `make e2e-test`: 17 passed (2.3m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. planning-target element exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- aggregate trigger surface에 남은 box-level `toContainText` 후보: capability/audit meta (recurrence count + relative timestamp와 합쳐진 span 구조) 등은 이번 슬라이스 범위 밖이며 selector/wording 리스크가 더 큽니다.

## 커밋

- `3a6bcec` test: tighten aggregate-trigger-planning-target to exact-text on dedicated element
