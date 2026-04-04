# file-summary initial response-text gate smoke tightening

날짜: 2026-04-05

## 목표

file-summary test의 initial branch readiness gate를 `response-box` container 대신 `response-text` 직접 참조로 변경합니다. document-summary family의 마지막 broad container gate를 닫습니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 126-127)
  - 기존: `await expect(page.getByTestId("response-box")).toContainText("중간 섹션 핵심 결정은 승인 기반 저장을 유지하는 것입니다.");`
  - 교체:
    - `await expect(page.getByTestId("response-text")).toBeVisible();`
    - `await expect(page.getByTestId("response-text")).toContainText(middleSignal);`
  - hardcoded string을 기존 top-level const `middleSignal`로 교체하여 일관성 확보

## 변경하지 않은 것

- line 160-161의 second-submit branch (이미 response-text gate)
- folder-search/search-only families (이미 response-text gate)
- verdict-state family, cancel family
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `make e2e-test`: **17 passed (4.2m)**

## python3 -m unittest 생략 사유

test-only Playwright stabilization 라운드이며 Python runtime/handler 코드는 수정하지 않았으므로 unit test를 생략합니다.

## document-summary response-text gate family 완료 상태

- line 127: file-summary initial ✓
- line 160-161: file-summary repeat-submit ✓
- line 194-195: folder-search summary ✓
- line 247: search-only pre-preview (selected-text gate) ✓
- line 295-296: search-only recovery ✓
- 전체 family 닫힘
