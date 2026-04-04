# response-correction-recorded-state-late-recorrect timestamp-pattern smoke tightening

날짜: 2026-04-04
슬라이스: response-correction-recorded-state-late-recorrect timestamp-pattern smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 corrected-save late reject / re-correct scenario의 `#response-correction-state` assertion 1건을 anchored regex pattern `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:532` — `toContainText("기록된 수정본이 있습니다")`를 `toHaveText(/^기록된 수정본이 있습니다 · .+$/)`로 교체

## 변경 내용

- 기존 line 532의 `toContainText`를 primary-flow(line 443), post-approval(line 502)와 동일한 anchored regex `toHaveText`로 대체했습니다.
- `#response-correction-state`의 recorded branch 세 지점(line 443, 502, 532)이 이제 모두 동일한 timestamp-pattern으로 검증됩니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n 'response-correction-state|기록된 수정본이 있습니다|입력창 변경이 아직 다시 기록되지 않았습니다' e2e/tests/web-smoke.spec.mjs`: line 443, 502, 532 pattern + line 459 toContainText 확인
- `make e2e-test`: 17 passed (2.8m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. recorded correction state timestamp-pattern 강화만 수행했으며 런타임 behavior 변경 없음.
- `#response-correction-state`의 unrecorded-change state(line 459)가 마지막 남은 `toContainText`입니다.

## 커밋

- `0668c8a` test: tighten response-correction-recorded-state-late-recorrect to timestamp-pattern on dedicated element
