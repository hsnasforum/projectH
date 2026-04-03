# aggregate-transition result notice full-match smoke tightening

날짜: 2026-04-04
슬라이스: aggregate-transition result notice full-match smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 aggregate result success notice assertion을 `canonical_transition_id` 기반 full-match로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:811` — payload fetch 후 `toHaveText(\`검토 메모 적용 결과가 확정되었습니다. (${...canonical_transition_id})\`)` 추가

## 변경 내용

- 기존 `toContainText("검토 메모 적용 결과가 확정되었습니다.")` (line 797)은 sync wait으로 유지하고, payload fetch 후 `resultAggregate.reviewed_memory_transition_record.canonical_transition_id`를 사용한 `toHaveText` full-match assertion을 추가했습니다.
- 런타임 `app/static/app.js:2753`의 `` `검토 메모 적용 결과가 확정되었습니다. (${data.canonical_transition_id})` `` 템플릿과 정확히 일치합니다.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `make e2e-test`: 17 passed (2.9m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. notice full-match 강화만 수행했으며 런타임 behavior 변경 없음.
- 남은 `#notice-box` `toContainText` assertions (stop, reversal, conflict)도 동일 패턴이며 이번 라운드 범위 밖.

## 커밋

- `56637b3` test: tighten aggregate-transition result notice to full-match with canonical_transition_id
