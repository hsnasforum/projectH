# rejected-verdict initial response-text gate smoke tightening

날짜: 2026-04-05

## 목표

rejected-verdict initial branch의 readiness gate를 `responseBox` container 대신 `response-text` 직접 참조로 변경합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 380-381)
  - 기존: `await expect(responseBox).toContainText("중간 섹션 핵심 결정은 승인 기반 저장을 유지하는 것입니다.");`
  - 교체:
    - `await expect(page.getByTestId("response-text")).toBeVisible();`
    - `await expect(page.getByTestId("response-text")).toContainText(middleSignal);`

## 변경하지 않은 것

- candidate-confirmation line 572 (아직 broad container gate)
- file-summary/browser-file-picker/folder-search/search-only families
- verdict-state family, cancel family
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `make e2e-test`: **17 passed (4.6m)**

## python3 -m unittest 생략 사유

test-only Playwright stabilization 라운드이며 Python runtime/handler 코드는 수정하지 않았으므로 unit test를 생략합니다.

## 잔여 리스크

- line 572 (candidate-confirmation) 아직 `responseBox` broad gate — 별도 슬라이스 대상
