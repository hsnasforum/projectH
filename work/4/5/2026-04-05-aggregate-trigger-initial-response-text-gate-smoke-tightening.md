# aggregate-trigger initial response-text gate smoke tightening

날짜: 2026-04-05

## 목표

aggregate-trigger scenario의 첫 번째 request readiness gate를 `response-box` broad container 대신 `response-text` 직접 참조로 변경합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 736-737)
  - 기존: `await expect(page.getByTestId("response-box")).toContainText(middleSignal);`
  - 교체:
    - `await expect(page.getByTestId("response-text")).toBeVisible();`
    - `await expect(page.getByTestId("response-text")).toContainText(middleSignal);`

## 변경하지 않은 것

- same-scenario second-request gate line 755 (아직 broad container gate)
- corrected-save family, cancel family, candidate-confirmation family
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `make e2e-test`: `127.0.0.1:8879` port-in-use로 차단됨 (이전 라운드와 동일 환경 문제)
- isolated alternate-port single-test rerun (`port 8893`):
  - `same-session recurrence aggregate는 separate blocked trigger surface로 렌더링됩니다` → `1 passed (46.4s)`

## python3 -m unittest 생략 사유

test-only Playwright stabilization 라운드이며 Python runtime/handler 코드는 수정하지 않았으므로 unit test를 생략합니다.

## 잔여 리스크

- canonical `make e2e-test` full-suite는 port 8879 충돌로 이번 라운드에서도 재현 불가
- readiness family의 남은 broad gate: aggregate-trigger second-request line 755
