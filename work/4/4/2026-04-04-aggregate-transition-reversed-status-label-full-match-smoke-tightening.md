# aggregate-transition reversed status-label full-match smoke tightening

날짜: 2026-04-04
슬라이스: aggregate-transition reversed status-label full-match smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 aggregate reversed status label(`aggregate-trigger-reversed` testid)에 대해 `canonical_transition_id` 기반 full-match assertion을 추가합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:861` — `toHaveText(\`적용 되돌림 완료 (${...canonical_transition_id})\`)` 추가

## 변경 내용

- 기존 `aggregate-trigger-reversed`의 `toBeVisible()` (line 849)과 aggregate box helper text `toContainText(...)` (line 850)는 유지하고, dedicated testid에 대한 `toHaveText` full-match assertion 1건을 추가했습니다.
- 런타임 `app/static/app.js:2614`의 `` `적용 되돌림 완료 (${String(transitionRecord.canonical_transition_id || "").trim()})` `` 템플릿과 정확히 일치합니다.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `make e2e-test`: 17 passed (2.2m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. status-label full-match 강화만 수행했으며 런타임 behavior 변경 없음.
- conflict-checked status label은 이번 라운드 범위 밖.

## 커밋

- `cee1391` test: tighten aggregate-transition reversed status-label to full-match with canonical_transition_id
