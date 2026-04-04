# corrected-save first-bridge snapshot-label response-text gate smoke tightening

날짜: 2026-04-05

## 목표

corrected-save first bridge path의 snapshot-label readiness gate를 `response-box` broad container 대신 `response-text` 직접 참조로 변경합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 480-481)
  - 기존: `await expect(page.getByTestId("response-box")).toContainText("현재 기록된 수정본 스냅샷");`
  - 교체:
    - `await expect(page.getByTestId("response-text")).toBeVisible();`
    - `await expect(page.getByTestId("response-text")).toContainText("현재 기록된 수정본 스냅샷");`

## 변경하지 않은 것

- lines 854/855 (다른 test의 broad gate)
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `make e2e-test`: `127.0.0.1:8879` port-in-use로 차단됨 (이전 라운드와 동일 환경 문제)
- isolated alternate-port single-test rerun (`port 8907`):
  - `corrected-save first bridge path가 기록본 기준 승인 스냅샷으로 저장됩니다` → `1 passed (18.1s)`

## python3 -m unittest 생략 사유

test-only Playwright stabilization 라운드이며 Python runtime/handler 코드는 수정하지 않았으므로 unit test를 생략합니다.

## 잔여 리스크

- canonical `make e2e-test` full-suite는 port 8879 충돌로 이번 라운드에서도 재현 불가
- 남은 broad `page.getByTestId("response-box")).toContainText(...)` gate: lines 854/855 (2건)
