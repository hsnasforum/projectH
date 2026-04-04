# corrected-save first-bridge resave-reminder response-text gate smoke tightening

날짜: 2026-04-05

## 목표

corrected-save first-bridge path의 resave-reminder assertion을 `response-box` broad container 대신 `response-text` 직접 참조로 변경합니다. 이것으로 corrected-save first-bridge path의 broad gate가 전부 닫힙니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 492)
  - 기존: `await expect(page.getByTestId("response-box")).toContainText("다시 저장 요청해 주세요.");`
  - 교체: `await expect(page.getByTestId("response-text")).toContainText("다시 저장 요청해 주세요.");`

## 변경하지 않은 것

- corrected-save first-bridge earlier lines 490-491 (이전 라운드에서 이미 변경됨)
- corrected-save long-history lines 521/531/551/623
- rejected-verdict family, late-flip family
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `make e2e-test`: `127.0.0.1:8879` port-in-use로 차단됨 (이전 라운드와 동일 환경 문제)
- isolated alternate-port single-test rerun (`port 8900`):
  - `corrected-save first bridge path가 기록본 기준 승인 스냅샷으로 저장됩니다` → `1 passed (19.2s)`

## python3 -m unittest 생략 사유

test-only Playwright stabilization 라운드이며 Python runtime/handler 코드는 수정하지 않았으므로 unit test를 생략합니다.

## 잔여 리스크

- canonical `make e2e-test` full-suite는 port 8879 충돌로 이번 라운드에서도 재현 불가
- 남은 broad `responseBox` gate: corrected-save long-history 521/531/551/623
