# browser-file-picker summary response-text gate smoke tightening

날짜: 2026-04-05

## 목표

browser-file-picker summary test의 readiness gate를 `response-box` container 대신 `response-text` 직접 참조로 변경합니다. summary-readiness family의 마지막 broad container gate를 닫습니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 178-179)
  - 기존: `await expect(page.getByTestId("response-box")).toContainText("중간 섹션 핵심 결정은 승인 기반 저장을 유지하는 것입니다.");`
  - 교체:
    - `await expect(page.getByTestId("response-text")).toBeVisible();`
    - `await expect(page.getByTestId("response-text")).toContainText(middleSignal);`

## 변경하지 않은 것

- file-summary initial/repeat-submit branches (이미 response-text gate)
- folder-search/search-only families (이미 response-text gate)
- verdict-state family, cancel family
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `make e2e-test`: **17 passed (5.0m)**

## python3 -m unittest 생략 사유

test-only Playwright stabilization 라운드이며 Python runtime/handler 코드는 수정하지 않았으므로 unit test를 생략합니다.

## summary-readiness response-text gate family 완료 상태

- line 127: file-summary initial ✓
- line 161-162: file-summary repeat-submit ✓
- line 179: browser-file-picker summary ✓
- line 195-196: folder-search summary ✓
- line 248: search-only pre-preview (selected-text gate) ✓
- line 296-297: search-only recovery ✓
- 전체 family 닫힘
