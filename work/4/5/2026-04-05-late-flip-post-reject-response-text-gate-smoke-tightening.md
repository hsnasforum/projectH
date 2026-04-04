# late-flip post-reject response-text gate smoke tightening

날짜: 2026-04-05

## 목표

late-flip scenario의 post-reject readiness gate를 `responseBox` broad container 대신 `response-text` 직접 참조로 변경합니다. 이것으로 late-flip scenario의 broad gate가 전부 닫힙니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 359-360)
  - 기존: `await expect(responseBox).toContainText("저장했습니다.");`
  - 교체:
    - `await expect(page.getByTestId("response-text")).toBeVisible();`
    - `await expect(page.getByTestId("response-text")).toContainText("저장했습니다.");`

## 변경하지 않은 것

- rejected-verdict line 428
- corrected-save lines 519/529/549/621
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `make e2e-test`: `127.0.0.1:8879` port-in-use로 차단됨 (이전 라운드와 동일 환경 문제)
- isolated alternate-port single-test rerun (`port 8897`):
  - `원문 저장 후 늦게 내용 거절해도 saved history와 latest verdict가 분리됩니다` → `1 passed (14.7s)`

## python3 -m unittest 생략 사유

test-only Playwright stabilization 라운드이며 Python runtime/handler 코드는 수정하지 않았으므로 unit test를 생략합니다.

## 잔여 리스크

- canonical `make e2e-test` full-suite는 port 8879 충돌로 이번 라운드에서도 재현 불가
- 남은 broad `responseBox` gate: rejected-verdict 428, corrected-save 519/529/549/621
