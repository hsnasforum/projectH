# corrected-save first-bridge save-result response-text gate smoke tightening

날짜: 2026-04-05

## 목표

corrected-save first-bridge path의 save-result readiness gate를 `response-box` broad container 대신 `response-text` 직접 참조로 변경합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 490-491)
  - 기존: `await expect(page.getByTestId("response-box")).toContainText("승인 시점에 고정된 수정본");`
  - 교체:
    - `await expect(page.getByTestId("response-text")).toBeVisible();`
    - `await expect(page.getByTestId("response-text")).toContainText("승인 시점에 고정된 수정본");`

## 변경하지 않은 것

- corrected-save line 492 ("다시 저장 요청해 주세요." broad assertion)
- corrected-save long-history lines 521/531/551/623
- rejected-verdict family, late-flip family
- runtime logic, template, docs

## 첫 시도 실패와 수정

첫 edit에서 한국어 문자열 "승인 시점에 고정된 수정본"이 유니코드 깨짐으로 mojibake 상태가 되어 테스트가 실패했습니다. 문자열을 정확히 수정한 뒤 재실행하여 통과했습니다.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `make e2e-test`: `127.0.0.1:8879` port-in-use로 차단됨 (이전 라운드와 동일 환경 문제)
- isolated alternate-port single-test rerun (`port 8899`):
  - 1차: mojibake로 실패
  - 2차 (수정 후): `corrected-save first bridge path가 기록본 기준 승인 스냅샷으로 저장됩니다` → `1 passed (18.2s)`

## python3 -m unittest 생략 사유

test-only Playwright stabilization 라운드이며 Python runtime/handler 코드는 수정하지 않았으므로 unit test를 생략합니다.

## 잔여 리스크

- canonical `make e2e-test` full-suite는 port 8879 충돌로 이번 라운드에서도 재현 불가
- 남은 broad `responseBox` gate: corrected-save 492 ("다시 저장 요청해 주세요."), long-history 521/531/551/623
