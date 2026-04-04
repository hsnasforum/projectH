# aggregate-trigger-section-label exact-text smoke tightening

날짜: 2026-04-04
슬라이스: aggregate-trigger-section-label exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 same-session recurrence aggregate scenario의 section label assertion을 box-level `toContainText`에서 dedicated `.sidebar-section-label` element exact-text `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:743` — `aggregateTriggerBox.locator(".sidebar-section-label")` 기준 `toHaveText("검토 메모 적용 후보")` 1건으로 교체

## 변경 내용

- 기존 line 743의 `await expect(aggregateTriggerBox).toContainText("검토 메모 적용 후보")`를 `await expect(aggregateTriggerBox.locator(".sidebar-section-label")).toHaveText("검토 메모 적용 후보")`로 교체했습니다.
- `.sidebar-section-label` element는 템플릿 `app/templates/index.html:29`에서 `#aggregate-trigger-box` 안에 정확히 `검토 메모 적용 후보`를 렌더링하는 요소입니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n '검토 메모 적용 후보|sidebar-section-label' e2e/tests/web-smoke.spec.mjs app/templates/index.html`: test 1건 + template 3건 확인
- `make e2e-test`: 17 passed (2.3m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. section label element exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- aggregate trigger surface에 남은 box-level `toContainText` 후보: capability/audit meta, planning-target copy 등은 이번 슬라이스 범위 밖입니다.

## 커밋

- `4b3aff2` test: tighten aggregate-trigger-section-label to exact-text on dedicated element
