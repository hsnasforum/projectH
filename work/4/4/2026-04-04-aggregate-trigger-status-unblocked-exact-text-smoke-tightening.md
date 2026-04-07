# aggregate-trigger-status unblocked exact-text smoke tightening

날짜: 2026-04-04
슬라이스: aggregate-trigger-status unblocked exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 same-session recurrence aggregate scenario의 unblocked status line을 dedicated `#aggregate-trigger-status` element 기준 exact-text assertion으로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:742` — `await expect(page.locator("#aggregate-trigger-status")).toHaveText("검토 메모 적용을 시작할 수 있는 묶음이 있습니다.");` 1건 추가

## 변경 내용

- aggregate box가 visible로 전환된 직후, dedicated `#aggregate-trigger-status` element에 대해 `toHaveText` exact-text assertion 1건을 추가했습니다.
- expected value는 런타임 `app/static/app.js:2526-2527`의 unblocked branch 전체 문자열 `검토 메모 적용을 시작할 수 있는 묶음이 있습니다.`와 정확히 일치합니다.
- 기존 box-level `toContainText` assertions는 그대로 유지했습니다.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n 'aggregate-trigger-status|검토 메모 적용을 시작할 수 있는 묶음이 있습니다' e2e/tests/web-smoke.spec.mjs app/static/app.js app/templates/index.html`: 4건 확인 (test 1, runtime 2, template 1)
- `make e2e-test`: 17 passed (3.2m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. status element exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- aggregate trigger surface에 남은 exact-text 후보: blocked status line, blocked helper 등은 이번 슬라이스 범위 밖입니다.

## 커밋

- `9581493` test: tighten aggregate-trigger-status unblocked to exact-text on dedicated element
