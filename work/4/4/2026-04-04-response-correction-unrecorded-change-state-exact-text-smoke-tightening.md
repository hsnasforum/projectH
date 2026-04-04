# response-correction-unrecorded-change-state exact-text smoke tightening

날짜: 2026-04-04
슬라이스: response-correction-unrecorded-change-state exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 unrecorded-change branch의 `#response-correction-state` assertion 1건을 exact-text `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:459` — `toContainText`를 `toHaveText("입력창 변경이 아직 다시 기록되지 않았습니다.")`로 교체

## 변경 내용

- 기존 line 459의 `toContainText`를 런타임 `app/static/app.js:1410`의 exact static string과 일치하는 `toHaveText`로 대체했습니다.
- `#response-correction-state`의 모든 assertion(recorded 3건 + unrecorded-change 1건)이 이제 모두 `toHaveText` 기준(exact-text 또는 anchored pattern)으로 검증됩니다.
- `#response-correction-state` family가 이 슬라이스로 닫혔습니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n 'response-correction-state|기록된 수정본이 있습니다|입력창 변경이 아직 다시 기록되지 않았습니다' e2e/tests/web-smoke.spec.mjs app/static/app.js`: test 4건 모두 toHaveText + runtime 다수 확인
- `make e2e-test`: 17 passed (2.8m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. unrecorded-change state exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- `#response-correction-status`의 unrecorded-change variant(line 460-461)는 아직 `toContainText`로 남아 있습니다.

## 커밋

- `5cb5319` test: tighten response-correction-unrecorded-change-state to exact-text on dedicated element
