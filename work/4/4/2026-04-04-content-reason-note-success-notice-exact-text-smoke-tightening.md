# content-reason-note success notice exact-text smoke tightening

날짜: 2026-04-04
슬라이스: content-reason-note success-notice exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 content-reason-note success notice assertion 2건을 `toContainText` → `toHaveText`로 강화하여, 런타임 고정 문자열과 정확히 일치하는지 검증합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:395` — `toContainText` → `toHaveText`
- `e2e/tests/web-smoke.spec.mjs:520` — `toContainText` → `toHaveText`

## 변경 내용

- "내용 거절은 approval을 유지하고 나중 explicit save로 supersede 됩니다" 테스트와 "corrected-save 저장 뒤 늦게 내용 거절하고 다시 수정해도…" 테스트 내 `#notice-box` assertion을 substring match에서 exact text match로 각각 강화했습니다.
- 런타임 소스 `app/static/app.js:2014`의 `renderNotice("거절 메모를 기록했습니다. 내용 거절 판정은 그대로 유지됩니다.")`와 정확히 일치합니다.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg` 교차 확인: runtime 고정 문자열과 smoke expected value 일치 (2건 smoke, 1건 runtime)
- `make e2e-test`: 17 passed (2.9m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- 남은 `toContainText` notice family (content-reject, aggregate transition, apply, reversal, conflict, cancel 등)는 이번 라운드 범위 밖.

## 커밋

- `ff0fc56` test: tighten content-reason-note success notice assertions to exact text
