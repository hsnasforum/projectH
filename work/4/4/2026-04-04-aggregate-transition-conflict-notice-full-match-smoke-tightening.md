# aggregate-transition conflict notice full-match smoke tightening

날짜: 2026-04-04
슬라이스: aggregate-transition conflict notice full-match smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 aggregate conflict success notice assertion을 `canonical_transition_id` 기반 full-match로 강화합니다. 이것은 `#notice-box` notice family smoke tightening 시리즈의 마지막 슬라이스입니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:887` — payload fetch 후 `toHaveText(\`충돌 확인이 완료되었습니다. (${...canonical_transition_id})\`)` 추가

## 변경 내용

- 기존 `toContainText("충돌 확인이 완료되었습니다.")` (line 864)은 sync wait으로 유지하고, payload fetch 후 `conflictAggregate.reviewed_memory_conflict_visibility_record.canonical_transition_id`를 사용한 `toHaveText` full-match assertion을 추가했습니다.
- 런타임 `app/static/app.js:2656`의 `` `충돌 확인이 완료되었습니다. (${data.canonical_transition_id})` `` 템플릿과 정확히 일치합니다.
- conflict는 `reviewed_memory_transition_record`가 아닌 `reviewed_memory_conflict_visibility_record`의 별도 `canonical_transition_id`를 사용하며, 이는 `app/handlers/aggregate.py:675`의 `conflict_transition_id`에서 유래합니다.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `make e2e-test`: 17 passed (3.0m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. notice full-match 강화만 수행했으며 런타임 behavior 변경 없음.
- 이 슬라이스로 `#notice-box` notice family의 모든 smoke tightening 후보가 닫혔습니다 (fixed exact-text: copy, correction-submit, candidate-confirmation, candidate-review-accept, corrected-save, content-reason-note, content-reject saved/unsaved, cancel / dynamic id: emitted, apply, result, stop, reversal, conflict).

## 커밋

- `75c9deb` test: tighten aggregate-transition conflict notice to full-match with canonical_transition_id
