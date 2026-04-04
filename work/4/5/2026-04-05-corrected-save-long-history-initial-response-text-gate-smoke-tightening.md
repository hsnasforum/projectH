# corrected-save long-history initial response-text gate smoke tightening

날짜: 2026-04-05

## 목표

corrected-save long-history scenario의 initial save-result readiness gate를 `responseBox` broad container 대신 `response-text` 직접 참조로 변경합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 521-522)
  - 기존: `await expect(responseBox).toContainText("승인 시점에 고정된 수정본");`
  - 교체:
    - `await expect(page.getByTestId("response-text")).toBeVisible();`
    - `await expect(page.getByTestId("response-text")).toContainText("승인 시점에 고정된 수정본");`

## 변경하지 않은 것

- same-scenario post-reject line 532
- same-scenario post-recorrect line 552
- candidate-confirmation sibling line 624
- corrected-save first-bridge path (이전 라운드에서 이미 완료)
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `make e2e-test`: `127.0.0.1:8879` port-in-use로 차단됨 (이전 라운드와 동일 환경 문제)
- isolated alternate-port single-test rerun (`port 8901`):
  - `corrected-save 저장 뒤 늦게 내용 거절하고 다시 수정해도 saved snapshot과 latest state가 분리됩니다` → `1 passed (26.2s)`

## python3 -m unittest 생략 사유

test-only Playwright stabilization 라운드이며 Python runtime/handler 코드는 수정하지 않았으므로 unit test를 생략합니다.

## 잔여 리스크

- canonical `make e2e-test` full-suite는 port 8879 충돌로 이번 라운드에서도 재현 불가
- 남은 broad `responseBox` gate: corrected-save long-history 532/552, candidate-confirmation sibling 624
