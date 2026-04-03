# content-reject unsaved success notice exact-text smoke tightening

날짜: 2026-04-04
슬라이스: content-reject unsaved success-notice exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 unsaved `content-reject` success notice assertion 1건을 `toContainText` → `toHaveText`로 강화하여, 런타임 고정 문자열과 정확히 일치하는지 검증합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:385` — `toContainText("내용 거절을 기록했습니다. 저장 승인 거절과는 별도입니다.")` → `toHaveText("내용 거절을 기록했습니다. 저장 승인 거절과는 별도입니다.")`

## 변경 내용

- "내용 거절은 approval을 유지하고 나중 explicit save로 supersede 됩니다" 테스트 내 `#notice-box` assertion을 substring match에서 exact text match로 강화했습니다.
- 런타임 소스 `app/static/app.js:1993`의 `savedHistoryExists = false` branch 고정 문자열과 정확히 일치합니다.
- 이로써 fixed exact message를 쓰는 `#notice-box` `toContainText` 후보가 모두 `toHaveText`로 전환 완료되었습니다.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg` 교차 확인: runtime 고정 문자열과 smoke expected value 일치 (1건 smoke, 1건 runtime)
- `make e2e-test`: 17 passed (2.9m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- 남은 `#notice-box` `toContainText` assertions (aggregate transition, apply, result, stop, reversal, conflict, cancel)는 transition id suffix 또는 server-provided message fallback이 얽혀 있어 단순 exact-text 전환 대상이 아닙니다.

## 커밋

- `3d5a293` test: tighten content-reject unsaved success notice assertion to exact text
