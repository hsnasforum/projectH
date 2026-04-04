# aggregate-trigger-title exact-text smoke tightening

날짜: 2026-04-04
슬라이스: aggregate-trigger-title exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 same-session recurrence aggregate scenario의 item title assertion을 box-level `toContainText`에서 dedicated element exact-text `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:744` — `aggregateTriggerBox.getByTestId("aggregate-trigger-item").locator("strong").first()` 기준 `toHaveText("반복 교정 묶음")` 1건으로 교체

## 변경 내용

- 기존 line 744의 `await expect(aggregateTriggerBox).toContainText("반복 교정 묶음")`을 `await expect(aggregateTriggerBox.getByTestId("aggregate-trigger-item").locator("strong").first()).toHaveText("반복 교정 묶음")`으로 교체했습니다.
- `<strong>` element는 런타임 `app/static/app.js:2543-2544`에서 `aggregateTriggerTitle(item)` 결과를 직접 렌더링하는 요소이며, `candidate_family === "correction_rewrite"`일 때 정확히 `반복 교정 묶음`을 반환합니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n '반복 교정 묶음|aggregateTriggerTitle|candidate_family' e2e/tests/web-smoke.spec.mjs app/static/app.js`: test 1건 + runtime 5건 확인
- `make e2e-test`: 17 passed (2.3m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. title element exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- aggregate trigger surface에 남은 box-level `toContainText` 후보: capability/audit meta, planning-target copy 등은 이번 슬라이스 범위 밖입니다.

## 커밋

- `2488931` test: tighten aggregate-trigger-title to exact-text on dedicated element
