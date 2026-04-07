# general-chat source-type-label response-text gate smoke tightening

날짜: 2026-04-06

## 목표

`e2e/tests/web-smoke.spec.mjs`의 general-chat test `일반 채팅 응답에는 source-type label이 붙지 않습니다`에서 마지막 남은 `response-box` broad readiness gate 1건을 `response-text` visible direct gate로 교체하여 smoke 안정성을 높입니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:949` — `response-box` not.toBeEmpty() → `response-text` toBeVisible()

## 변경 내용

- line 949의 `await expect(page.getByTestId("response-box")).not.toBeEmpty()` 를 `await expect(page.getByTestId("response-text")).toBeVisible()` 로 교체
- runtime `app/static/app.js:3153-3167`에서 `responseText.textContent`가 먼저 채워지므로 `response-text` visible이 더 deterministic한 gate입니다
- 이 변경으로 `response-box` broad readiness gate family 전체가 `response-text` direct gate로 전환 완료됩니다

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 문제 없음
- `make e2e-test`: `127.0.0.1:8879` port-in-use 충돌로 blocked (기존 서버 프로세스 점유)
- isolated alternate-port(8899) single-test rerun: `1 passed (9.2s)` 통과
  - test title: `일반 채팅 응답에는 source-type label이 붙지 않습니다`
- `python3 -m unittest -v tests.test_web_app`: 생략 (test-only Playwright stabilization 라운드, runtime 미변경)

## canonical make e2e-test blockage 사유

`127.0.0.1:8879`에 기존 서버 프로세스가 점유 중이어서 Playwright webServer launch가 실패합니다. unrelated server를 임의로 종료하지 않고 isolated alternate-port rerun으로 대체 검증했습니다.

## 커밋

- `effbd83` test: use response-text as direct gate for general-chat source-type-label readiness

## 잔여 위험

- `response-box` 참조는 파일 내 4건 남아 있으나, 모두 readiness gate가 아닌 element reference 용도입니다
- canonical `make e2e-test` port 충돌은 환경 이슈로, 이 슬라이스와 무관합니다

## 사용 스킬

- 없음 (단순 test-only 1-line gate 교체)
