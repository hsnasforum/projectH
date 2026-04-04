# candidate-confirmation save-result response-text gate smoke tightening

날짜: 2026-04-05

## 목표

candidate-confirmation path의 save-result readiness gate를 `responseBox` broad container 대신 `response-text` 직접 참조로 변경합니다. 이것으로 전체 `responseBox.toContainText(...)` broad gate family가 전부 닫힙니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 626-627)
  - 기존: `await expect(responseBox).toContainText("승인 시점에 고정된 수정본");`
  - 교체:
    - `await expect(page.getByTestId("response-text")).toBeVisible();`
    - `await expect(page.getByTestId("response-text")).toContainText("승인 시점에 고정된 수정본");`

## 변경하지 않은 것

- corrected-save long-history lines (이전 라운드에서 이미 완료)
- candidate-confirmation initial lines (이전 라운드에서 이미 완료)
- runtime logic, template, docs

## broad gate family 완료 상태

변경 후 `rg -n "responseBox).toContainText" e2e/tests/` 결과 0건입니다. 전체 `responseBox` broad container를 통한 `toContainText` gate가 모두 `response-text` 직접 참조로 변경 완료되었습니다.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `make e2e-test`: `127.0.0.1:8879` port-in-use로 차단됨 (이전 라운드와 동일 환경 문제)
- isolated alternate-port single-test rerun (`port 8904`):
  - `candidate confirmation path는 save support와 분리되어 기록되고 later correction으로 current state에서 사라집니다` → `1 passed (31.7s)`

## python3 -m unittest 생략 사유

test-only Playwright stabilization 라운드이며 Python runtime/handler 코드는 수정하지 않았으므로 unit test를 생략합니다.

## 잔여 리스크

- canonical `make e2e-test` full-suite는 port 8879 충돌로 이번 라운드에서도 재현 불가
- `responseBox` broad gate family는 이 라운���로 전부 닫힘 — 이 stabilization 시리즈 종료
