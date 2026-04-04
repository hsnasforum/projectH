# response-correction-recorded-state-primary-flow timestamp-pattern smoke tightening

날짜: 2026-04-04
슬라이스: response-correction-recorded-state-primary-flow timestamp-pattern smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 first correction-recorded point의 `#response-correction-state` assertion 1건을 anchored regex pattern `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:443` — `toContainText("기록된 수정본이 있습니다")`를 `toHaveText(/^기록된 수정본이 있습니다 · .+$/)`로 교체

## 변경 내용

- 기존 line 443의 `toContainText`를 anchored regex `toHaveText(/^기록된 수정본이 있습니다 · .+$/)`로 대체했습니다.
- 런타임 `app/static/app.js:1427-1429`에서 recorded correction state는 `기록된 수정본이 있습니다 · ${formatWhen(...)}`로 렌더링되므로, timestamp-bearing branch임을 확인하면서도 dynamic timestamp 값 자체는 `.+`로 허용합니다.
- candidate confirmation recorded-state(line 630)와 동일한 timestamp-pattern 패턴입니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n 'response-correction-state|기록된 수정본이 있습니다|입력창 변경이 아직 다시 기록되지 않았습니다' e2e/tests/web-smoke.spec.mjs app/templates/index.html app/static/app.js`: test + runtime 다수 확인
- `make e2e-test`: 17 passed (2.8m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. recorded correction state timestamp-pattern 강화만 수행했으며 런타임 behavior 변경 없음.
- `#response-correction-state`의 later recorded-state duplicates(line 502, 532)와 unrecorded-change state(line 459)는 아직 `toContainText`로 남아 있습니다.

## 커밋

- `6a6baea` test: tighten response-correction-recorded-state-primary-flow to timestamp-pattern on dedicated element
