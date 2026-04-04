# late-flip initial response-text gate smoke tightening

날짜: 2026-04-05

## 목표

late-flip scenario의 initial save-result readiness gate를 `responseBox` broad container 대신 `response-text` 직접 참조로 변경합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 347-348)
  - 기존: `await expect(responseBox).toContainText("저장했습니다.");`
  - 교체:
    - `await expect(page.getByTestId("response-text")).toBeVisible();`
    - `await expect(page.getByTestId("response-text")).toContainText("저장했습니다.");`

## 변경하지 않은 것

- same-scenario post-reject line 359
- rejected-verdict line 427
- corrected-save lines 518/528/548/620
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `make e2e-test`: `127.0.0.1:8879` port-in-use로 차단됨 (이전 라운드와 동일 환경 문제)
- isolated alternate-port single-test rerun (`port 8896`):
  - `원문 저장 후 늦게 내용 거절해도 saved history와 latest verdict가 분리됩니다` → `1 passed (15.5s)`

## python3 -m unittest 생략 사유

test-only Playwright stabilization 라운드이며 Python runtime/handler 코드는 수정하지 않았으므로 unit test를 생략합니다.

## 잔여 리스크

- canonical `make e2e-test` full-suite는 port 8879 충돌로 이번 라운드에서도 재현 불가
- 남은 broad `responseBox` gate: late-flip post-reject 359, rejected-verdict 427, corrected-save 518/528/548/620
