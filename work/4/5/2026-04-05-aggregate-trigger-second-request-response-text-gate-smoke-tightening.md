# aggregate-trigger second-request response-text gate smoke tightening

날짜: 2026-04-05

## 목표

aggregate-trigger scenario의 두 번째 request readiness gate를 `response-box` broad container 대신 `response-text` 직접 참조로 변경합니다. 이것으로 `middleSignal` broad gate family가 전부 닫힙니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 755-756)
  - 기존: `await expect(page.getByTestId("response-box")).toContainText(middleSignal);`
  - 교체:
    - `await expect(page.getByTestId("response-text")).toBeVisible();`
    - `await expect(page.getByTestId("response-text")).toContainText(middleSignal);`

## 변경하지 않은 것

- initial request gate (이전 라운드에서 이미 변경됨)
- corrected-save family, cancel family, candidate-confirmation family
- runtime logic, template, docs

## middleSignal broad gate family 완료 상태

변경 후 `rg -n "toContainText(middleSignal)" e2e/tests/` 결과, 모든 7건이 `response-text` 직접 참조입니다. `response-box` broad container를 통한 middleSignal gate는 0건입니다.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `make e2e-test`: `127.0.0.1:8879` port-in-use로 차단됨 (이전 라운드와 동일 환경 문제)
- isolated alternate-port single-test rerun (`port 8894`):
  - `same-session recurrence aggregate는 separate blocked trigger surface로 렌더링됩니다` → `1 passed (46.4s)`

## python3 -m unittest 생략 사유

test-only Playwright stabilization 라운드이며 Python runtime/handler 코드는 수정하지 않았으므로 unit test를 생략합니다.

## 잔여 리스크

- canonical `make e2e-test` full-suite는 port 8879 충돌로 이번 라운드에서도 재현 불가
- `middleSignal` broad gate family는 이 라운드로 전부 닫힘
