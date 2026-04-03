# aggregate-transition result status-label full-match smoke tightening

날짜: 2026-04-04
슬라이스: aggregate-transition result status-label full-match smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 aggregate result status label(`aggregate-trigger-result` testid)에 대해 `canonical_transition_id`와 `applied_effect_kind` 기반 full-match assertion을 추가합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:814` — `toHaveText(\`결과 확정 완료 (${...canonical_transition_id} · ${...applied_effect_kind})\`)` 추가

## 변경 내용

- 기존 `aggregate-trigger-result`의 `toBeVisible()` (line 813)과 aggregate box helper text `toContainText("검토 메모 적용 효과가 활성화되었습니다.")` (line 815)는 유지하고, dedicated testid에 대한 `toHaveText` full-match assertion 1건을 추가했습니다.
- 런타임 `app/static/app.js:2706`의 `` `결과 확정 완료 (${id}${appliedEffect ? ` · ${appliedEffect}` : ""})` `` 템플릿과 정확히 일치합니다.
- 테스트가 이미 읽는 `resultAggregate.reviewed_memory_transition_record.canonical_transition_id`와 `apply_result.applied_effect_kind`를 사용합니다.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `make e2e-test`: 1차 실행에서 unrelated flaky (test 11 candidate confirmation path) 1건 발생, 2차 재실행에서 17 passed (2.1m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. status-label full-match 강화만 수행했으며 런타임 behavior 변경 없음.
- stopped/reversed/conflict-checked status labels는 이번 라운드 범위 밖.

## 커밋

- `9c6ad3c` test: tighten aggregate-transition result status-label to full-match with canonical_transition_id and applied_effect_kind
