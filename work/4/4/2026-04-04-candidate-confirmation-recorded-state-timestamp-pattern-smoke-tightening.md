# candidate-confirmation-recorded-state timestamp-pattern smoke tightening

날짜: 2026-04-04
슬라이스: candidate-confirmation-recorded-state timestamp-pattern smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 confirmation click 직후 recorded 상태의 `#response-candidate-confirmation-state` assertion 1건을 anchored regex pattern `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:630` — `toContainText("재사용 확인 기록됨")`를 `toHaveText(/^재사용 확인 기록됨 · .+$/)`로 교체

## 변경 내용

- 기존 line 630의 `toContainText`를 anchored regex `toHaveText(/^재사용 확인 기록됨 · .+$/)`로 대체했습니다.
- 런타임 `app/static/app.js:1509`에서 `latestCandidateConfirmationRecordedAt`가 있으면 `재사용 확인 기록됨 · ${formatWhen(...)}`를 렌더링하므로, timestamp-bearing branch임을 확인하면서도 dynamic timestamp 값 자체는 `.+`로 허용합니다.
- `#response-candidate-confirmation-state`의 두 상태(recorded line 630, no-confirmation line 695)가 이제 모두 `toHaveText` 기준(exact-text 또는 anchored pattern)으로 검증됩니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n 'response-candidate-confirmation-state|현재 수정 방향 재사용 확인은 아직 없습니다|재사용 확인 기록됨' e2e/tests/web-smoke.spec.mjs app/templates/index.html app/static/app.js`: test 2건 + runtime 다수 확인
- `make e2e-test`: 17 passed (2.6m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. recorded state label timestamp-pattern 강화만 수행했으며 런타임 behavior 변경 없음.
- candidate confirmation family의 `#response-candidate-confirmation-state`와 `#response-candidate-confirmation-status` assertions가 모두 exact-text 또는 anchored pattern으로 닫혔습니다.

## 커밋

- `cfffe7e` test: tighten candidate-confirmation-recorded-state to timestamp-pattern on dedicated element
