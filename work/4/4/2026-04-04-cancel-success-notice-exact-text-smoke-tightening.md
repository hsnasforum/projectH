# cancel success-notice exact-text smoke tightening

날짜: 2026-04-04
슬라이스: cancel success-notice exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 cancel success notice assertion 1건을 `toContainText` → `toHaveText`로 강화하고, expected value를 서버 발행 고정 메시지 전문으로 확장합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:892` — `toContainText("요청을 취소했습니다.")` → `toHaveText("요청을 취소했습니다. 현재까지 받은 응답만 화면에 남겨둡니다.")`

## 변경 내용

- "스트리밍 중 취소 버튼이 동작합니다" 테스트 내 `#notice-box` assertion을 substring match에서 exact text match로 강화했습니다.
- 서버 소스 `app/handlers/chat.py:97`의 cancelled event message `"요청을 취소했습니다. 현재까지 받은 응답만 화면에 남겨둡니다."`가 클라이언트 `app/static/app.js:783`의 `renderNotice(data.message || ...)` 경로를 통해 그대로 렌더링되는 것과 정확히 일치합니다.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg` 교차 확인: 서버 고정 메시지, 클라이언트 fallback, smoke expected value 일치
- `make e2e-test`: 17 passed (3.1m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- 남은 `#notice-box` `toContainText` assertions (aggregate transition, apply, result, stop, reversal, conflict)는 `canonical_transition_id` suffix가 동적으로 붙는 family로, 단순 exact-text 전환 대상이 아닙니다.

## 커밋

- `7c0cfde` test: tighten cancel success notice assertion to exact text
