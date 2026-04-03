# aggregate-transition emitted-record notice full-match smoke tightening

날짜: 2026-04-04
슬라이스: aggregate-transition emitted-record notice full-match smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 aggregate emitted-record success notice assertion을 `canonical_transition_id` 기반 full-match로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:775` — payload fetch 후 `toHaveText(\`transition record가 발행되었습니다. (${...canonical_transition_id})\`)` 추가

## 변경 내용

- 기존 `toContainText("transition record가 발행되었습니다.")` (line 761)은 sync wait으로 유지하되, payload fetch 후 `canonical_transition_id`를 사용한 `toHaveText` full-match assertion을 추가했습니다.
- 런타임 `app/static/app.js:2821`의 `` `transition record가 발행되었습니다. (${data.canonical_transition_id})` `` 템플릿과 정확히 일치합니다.
- 초기 시도에서 sync wait을 제거하니 payload fetch timing 문제로 실패했습니다. `toContainText`를 sync wait으로 복원하고 뒤에 `toHaveText` full-match를 추가하는 구조로 해결했습니다.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg` 교차 확인: runtime 템플릿과 smoke expected value 일치
- `make e2e-test`: 17 passed (2.8m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. notice full-match 강화만 수행했으며 런타임 behavior 변경 없음.
- 남은 `#notice-box` `toContainText` assertions (apply, result, stop, reversal, conflict)도 동일한 `canonical_transition_id` suffix 패턴이며 이번 라운드 범위 밖.

## 커밋

- `e943b6b` test: tighten aggregate-transition emitted-record notice to full-match with canonical_transition_id
