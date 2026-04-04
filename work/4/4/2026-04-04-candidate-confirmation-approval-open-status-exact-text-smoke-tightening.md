# candidate-confirmation-approval-open-status exact-text smoke tightening

날짜: 2026-04-04
슬라이스: candidate-confirmation-approval-open-status exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 save request click 뒤 approval-open 상태의 `#response-candidate-confirmation-status` assertion 1건을 full three-sentence exact-text `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:593` — `toContainText("이미 열린 저장 승인 카드와도 섞이지 않습니다.")`를 full `toHaveText("이 버튼은 현재 기록된 수정 방향을 나중에도 다시 써도 된다는 positive reuse confirmation만 남깁니다. 저장 승인, 내용 거절, 거절 메모, 피드백과는 별도입니다. 이미 열린 저장 승인 카드와도 섞이지 않습니다.")`로 교체

## 변경 내용

- 기존 line 593의 third sentence만 확인하던 `toContainText`를 런타임 `app/static/app.js:1524-1529`의 three-sentence approval-open variant 전체와 정확히 일치하는 `toHaveText`로 대체했습니다.
- 이제 `#response-candidate-confirmation-status`에 대한 세 가지 상태(pre-record line 564, approval-open line 593, recorded line 632)가 모두 full exact-text로 검증됩니다.
- candidate confirmation status family가 이 슬라이스로 닫혔습니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n 'response-candidate-confirmation-status|positive reuse confirmation만 남깁니다|이미 열린 저장 승인 카드와도 섞이지 않습니다' e2e/tests/web-smoke.spec.mjs app/templates/index.html app/static/app.js`: test 3건 + runtime 다수 확인
- `make e2e-test`: 17 passed (2.5m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. candidate confirmation approval-open status exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- candidate confirmation `#response-candidate-confirmation-status` family는 pre-record, approval-open, recorded 세 상태 모두 full exact-text로 닫혔습니다.

## 커밋

- `319ab44` test: tighten candidate-confirmation-approval-open-status to exact-text on dedicated element
