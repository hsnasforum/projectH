# file-summary repeat-submit response-text gate smoke tightening

날짜: 2026-04-05

## 목표

file-summary test의 second-submit branch readiness gate를 `response-box` container 대신 `response-text` 직접 참조로 변경합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 159-160)
  - 기존: `await expect(page.getByTestId("response-box")).toContainText(middleSignal);`
  - 교체:
    - `await expect(page.getByTestId("response-text")).toBeVisible();`
    - `await expect(page.getByTestId("response-text")).toContainText(middleSignal);`

## 변경하지 않은 것

- line 126의 initial summary gate
- search-only/folder-search families
- verdict-state family, cancel family
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `make e2e-test`: **17 passed (4.2m)**

## python3 -m unittest 생략 사유

test-only Playwright stabilization 라운드이며 Python runtime/handler 코드는 수정하지 않았으므로 unit test를 생략합니다.
