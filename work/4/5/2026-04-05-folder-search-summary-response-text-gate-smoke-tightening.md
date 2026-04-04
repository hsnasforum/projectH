# folder-search summary response-text gate smoke tightening

날짜: 2026-04-05

## 목표

folder-search summary test의 readiness gate를 `response-box` container 대신 `response-text` 직접 참조로 변경합니다. search-summary family의 마지막 broad container gate를 닫습니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 193-194)
  - 기존: `await expect(page.getByTestId("response-box")).toContainText("[모의 요약]");`
  - 교체:
    - `await expect(page.getByTestId("response-text")).toBeVisible();`
    - `await expect(page.getByTestId("response-text")).toContainText("[모의 요약]");`

## 변경하지 않은 것

- line 246의 search-only pre-preview gate
- line 294-295의 search-plus-summary recovery gate
- verdict-state family, cancel family
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `make e2e-test`: **17 passed (4.6m)**

## python3 -m unittest 생략 사유

test-only Playwright stabilization 라운드이며 Python runtime/handler 코드는 수정하지 않았으므로 unit test를 생략합니다.
