# response-correction-no-recorded-status exact-text smoke tightening

날짜: 2026-04-04
슬라이스: response-correction-no-recorded-status exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 initial correction 상태의 `#response-correction-status` assertion 2건을 1건의 exact-text `toHaveText`로 묶어 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:435` — 기존 2건의 `toContainText`를 1건의 `toHaveText("먼저 수정본 기록을 눌러야 저장 요청 버튼이 켜집니다. 입력창의 미기록 텍스트는 바로 승인 스냅샷이 되지 않습니다. 저장 승인과는 별도입니다.")`로 교체

## 변경 내용

- 기존 line 435-436의 두 `toContainText` assertion을 런타임 `app/static/app.js:1401-1405`의 three-sentence initial correction-status copy와 정확히 일치하는 단일 `toHaveText`로 대체했습니다.
- correction record가 없는 stable static state이므로 full exact-text가 가능합니다.
- candidate confirmation family가 닫힌 뒤 새로운 response-correction quality axis로 전환한 첫 슬라이스입니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n 'response-correction-status|먼저 수정본 기록을 눌러야|미기록 텍스트는 바로 승인 스냅샷이 되지 않습니다|저장 승인과는 별도입니다' e2e/tests/web-smoke.spec.mjs app/templates/index.html app/static/app.js`: test + runtime 다수 확인
- `make e2e-test`: 17 passed (2.6m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. initial correction status exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- `#response-correction-status`의 recorded/unrecorded-change variants(line 444, 460-461, 533)는 아직 `toContainText`로 남아 있습니다.

## 커밋

- `4e9c586` test: tighten response-correction-no-recorded-status to exact-text on dedicated element
