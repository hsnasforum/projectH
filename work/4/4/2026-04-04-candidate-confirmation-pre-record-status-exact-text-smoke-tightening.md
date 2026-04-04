# candidate-confirmation-pre-record-status exact-text smoke tightening

날짜: 2026-04-04
슬라이스: candidate-confirmation-pre-record-status exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 correction submit 직후 pre-record 상태의 `#response-candidate-confirmation-status` assertion 2건을 1건의 exact-text `toHaveText`로 묶어 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:564` — 기존 2건의 `toContainText`를 1건의 `toHaveText("이 버튼은 현재 기록된 수정 방향을 나중에도 다시 써도 된다는 positive reuse confirmation만 남깁니다. 저장 승인, 내용 거절, 거절 메모, 피드백과는 별도입니다.")`로 교체

## 변경 내용

- 기존 line 564-565의 두 `toContainText` assertion을 런타임 `app/static/app.js:1524-1526`의 two-sentence pre-record copy와 정확히 일치하는 단일 `toHaveText`로 대체했습니다.
- 이 scenario에서는 approval-open 이전이라 optional third sentence(`이미 열린 저장 승인 카드와도 섞이지 않습니다.`)가 없는 stable two-sentence state이므로 full exact-text가 가능합니다.
- line 593의 approval-open third sentence scenario는 이번 범위 밖입니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n 'response-candidate-confirmation-status|positive reuse confirmation만 남깁니다|저장 승인, 내용 거절, 거절 메모, 피드백과는 별도입니다' e2e/tests/web-smoke.spec.mjs app/templates/index.html app/static/app.js`: test + runtime 다수 확인
- `make e2e-test`: 17 passed (2.5m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. candidate confirmation pre-record status exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- candidate confirmation family에서 남은 broad check: line 593의 approval-open third sentence `toContainText` 1건.

## 커밋

- `3901d1d` test: tighten candidate-confirmation-pre-record-status to exact-text on dedicated element
