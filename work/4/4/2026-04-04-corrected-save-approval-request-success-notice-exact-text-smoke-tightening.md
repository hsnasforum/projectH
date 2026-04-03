# corrected-save approval-request success notice exact-text smoke tightening

날짜: 2026-04-04
슬라이스: corrected-save approval-request success-notice exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 corrected-save approval-request success notice assertion 1건을 `toContainText` → `toHaveText`로 강화하여, 런타임 고정 문자열과 정확히 일치하는지 검증합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:449` — `toContainText("기록된 수정본 기준 저장 승인을 만들었습니다.")` → `toHaveText("기록된 수정본 기준 저장 승인을 만들었습니다.")`

## 변경 내용

- corrected-save first bridge path 테스트 내 `#notice-box` assertion을 substring match에서 exact text match로 1건 강화했습니다.
- 런타임 소스 `app/static/app.js:2036`의 `renderNotice("기록된 수정본 기준 저장 승인을 만들었습니다.")`와 정확히 일치합니다.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg` 교차 확인: runtime 고정 문자열과 smoke expected value 일치
- `make e2e-test`: 17 passed (3.0m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- 남은 `toContainText` notice family (content-reject, 거절 메모, aggregate transition, cancel 등)는 이번 라운드 범위 밖.

## 커밋

- `5b1006e` test: tighten corrected-save approval-request success notice assertion to exact text
