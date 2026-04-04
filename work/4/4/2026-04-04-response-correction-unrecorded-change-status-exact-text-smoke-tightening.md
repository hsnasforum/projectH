# response-correction-unrecorded-change-status exact-text smoke tightening

날짜: 2026-04-04
슬라이스: response-correction-unrecorded-change-status exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 unrecorded-change branch의 `#response-correction-status` assertion 2건을 1건의 exact-text `toHaveText`로 묶어 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:460` — 기존 2건의 `toContainText`를 1건의 `toHaveText("저장 요청 버튼은 직전 기록본으로만 동작합니다. 지금 입력 중인 수정으로 저장하려면 먼저 수정본 기록을 다시 눌러 주세요. 저장 승인과는 별도입니다. 이미 열린 저장 승인 카드도 이전 요청 시점 스냅샷으로 그대로 유지됩니다.")`로 교체

## 변경 내용

- 기존 line 460-461의 두 `toContainText` assertion을 런타임 `app/static/app.js:1411-1418`의 four-sentence unrecorded-change status copy와 정확히 일치하는 단일 `toHaveText`로 대체했습니다.
- `#response-correction-status`의 모든 assertion(no-recorded line 435, recorded-primary line 444, unrecorded-change line 460, recorded-late-recorrect line 532)이 이제 모두 `toHaveText` exact-text로 검증됩니다.
- `#response-correction-status` family와 `#response-correction-state` family가 모두 이 슬라이스로 닫혔습니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n 'response-correction-status|저장 요청 버튼은 직전 기록본으로만 동작합니다|이미 열린 저장 승인 카드도 이전 요청 시점 스냅샷으로 그대로 유지됩니다' e2e/tests/web-smoke.spec.mjs app/static/app.js`: test 4건 모두 toHaveText + runtime 다수 확인
- `make e2e-test`: 17 passed (3.0m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. unrecorded-change status exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- response-correction family(`#response-correction-state` + `#response-correction-status`)가 완전히 닫혔습니다.

## 커밋

- `9716858` test: tighten response-correction-unrecorded-change-status to exact-text on dedicated element
