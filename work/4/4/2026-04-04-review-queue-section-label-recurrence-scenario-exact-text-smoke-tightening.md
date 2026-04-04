# review-queue-section-label-recurrence-scenario exact-text smoke tightening

날짜: 2026-04-04
슬라이스: review-queue-section-label-recurrence-scenario exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 same-session recurrence aggregate scenario의 review queue section label assertion을 box-level `toContainText`에서 dedicated `.sidebar-section-label` element exact-text `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:730` — `reviewQueueBox.locator(".sidebar-section-label")` 기준 `toHaveText("검토 후보")` 1건으로 교체

## 변경 내용

- 기존 line 730의 `await expect(reviewQueueBox).toContainText("검토 후보")`를 `await expect(reviewQueueBox.locator(".sidebar-section-label")).toHaveText("검토 후보")`로 교체했습니다.
- 이전 슬라이스(line 636)와 동일한 selector/exact-text 패턴을 recurrence scenario에 확장한 것입니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n '검토 후보|sidebar-section-label|review-queue-box' e2e/tests/web-smoke.spec.mjs app/templates/index.html`: line 636 + 730 모두 dedicated element exact-text 확인
- `make e2e-test`: 17 passed (2.4m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. review queue section label element exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- review queue `검토 후보` section label은 이제 두 scenario(line 636, 730) 모두 dedicated element exact-text로 검증됩니다.

## 커밋

- `d6a5d43` test: tighten review-queue-section-label in recurrence scenario to exact-text on dedicated element
