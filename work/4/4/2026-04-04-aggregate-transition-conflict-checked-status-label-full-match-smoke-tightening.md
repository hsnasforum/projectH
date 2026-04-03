# aggregate-transition conflict-checked status-label full-match smoke tightening

날짜: 2026-04-04
슬라이스: aggregate-transition conflict-checked status-label full-match smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 aggregate conflict-checked status label(`aggregate-trigger-conflict-checked` testid)에 대해 `canonical_transition_id`와 `conflict_entry_count` 기반 full-match assertion을 추가합니다. 이것은 aggregate dedicated status-label smoke tightening 시리즈의 마지막 슬라이스입니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:891` — `toHaveText(\`충돌 확인 완료 (${...canonical_transition_id} · 항목 ${...conflict_entry_count}건)\`)` 추가

## 변경 내용

- 기존 `aggregate-trigger-conflict-checked`의 `toBeVisible()` (line 869)과 aggregate box helper text `toContainText(...)` (line 870)는 유지하고, dedicated testid에 대한 `toHaveText` full-match assertion 1건을 추가했습니다.
- 런타임 `app/static/app.js:2623`의 `` `충돌 확인 완료 (${String(conflictVisibilityRecord.canonical_transition_id || "").trim()} · 항목 ${entryCount}건)` `` 템플릿과 정확히 일치합니다.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `make e2e-test`: 17 passed (2.6m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. status-label full-match 강화만 수행했으며 런타임 behavior 변경 없음.
- 이 슬라이스로 aggregate dedicated status-label family의 모든 smoke tightening 후보가 닫혔습니다 (result, stopped, reversed, conflict-checked).

## 커밋

- `92a4f6e` test: tighten aggregate-transition conflict-checked status-label to full-match with canonical_transition_id and conflict_entry_count
