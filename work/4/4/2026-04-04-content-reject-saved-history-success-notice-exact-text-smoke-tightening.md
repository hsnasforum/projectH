# content-reject saved-history success notice exact-text smoke tightening

날짜: 2026-04-04
슬라이스: content-reject saved-history success-notice exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 saved-history `content-reject` success notice assertion 2건을 `toContainText` → `toHaveText`로 강화하고, expected value를 런타임 `savedHistoryExists = true` branch 고정 문자열 전문으로 확장합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:351` — `toContainText("이미 저장된 노트는 그대로 유지되며 최신 내용 판정만 바뀝니다.")` → `toHaveText("내용 거절을 기록했습니다. 이미 저장된 노트는 그대로 유지되며 최신 내용 판정만 바뀝니다.")`
- `e2e/tests/web-smoke.spec.mjs:510` — 동일 변경

## 변경 내용

- "원문 저장 후 늦게 내용 거절해도…" 테스트와 "corrected-save 저장 뒤 늦게 내용 거절하고…" 테스트 내 `#notice-box` assertion을 substring match에서 exact text match로 각각 강화했습니다.
- 기존 expected value는 메시지 후반부만 매칭했으나, 런타임 소스 `app/static/app.js:1992`의 전체 고정 문자열 `"내용 거절을 기록했습니다. 이미 저장된 노트는 그대로 유지되며 최신 내용 판정만 바뀝니다."`로 exact match합니다.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg` 교차 확인: runtime 고정 문자열과 smoke expected value 일치 (2건 smoke, 1건 runtime)
- `make e2e-test`: 17 passed (3.2m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- unsaved `content-reject` variant (line 385)는 별도 exact string이라 이번 라운드에서 제외.
- 남은 `toContainText` notice family (aggregate transition, apply, reversal, conflict, cancel 등)는 이번 라운드 범위 밖.

## 커밋

- `726c224` test: tighten content-reject saved-history success notice assertions to exact text
