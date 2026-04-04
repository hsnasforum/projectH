# candidate-confirmation-no-confirmation-state exact-text smoke tightening

날짜: 2026-04-04
슬라이스: candidate-confirmation-no-confirmation-state exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 later correction 뒤 no-confirmation 상태의 `#response-candidate-confirmation-state` assertion 1건을 exact-text `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:695` — `toContainText`를 `toHaveText("현재 수정 방향 재사용 확인은 아직 없습니다.")`로 교체

## 변경 내용

- 기존 line 695의 `toContainText`를 런타임 `app/static/app.js:1523`의 fixed string과 정확히 일치하는 `toHaveText`로 대체했습니다.
- timestamp나 variant가 없는 stable static state이므로 full exact-text가 가능합니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n 'response-candidate-confirmation-state|현재 수정 방향 재사용 확인은 아직 없습니다|재사용 확인 기록됨' e2e/tests/web-smoke.spec.mjs app/templates/index.html app/static/app.js`: test 2건 + runtime 다수 확인
- `make e2e-test`: 17 passed (2.5m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. no-confirmation state label exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- `#response-candidate-confirmation-state`의 recorded 상태(line 630)는 `재사용 확인 기록됨 · {timestamp}` 형식으로 dynamic part가 있어 아직 `toContainText`로 남아 있습니다.

## 커밋

- `95d6e68` test: tighten candidate-confirmation-no-confirmation-state to exact-text on dedicated element
