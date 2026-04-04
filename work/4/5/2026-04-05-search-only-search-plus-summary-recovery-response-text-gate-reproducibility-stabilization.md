# search-only search-plus-summary recovery response-text gate reproducibility stabilization

날짜: 2026-04-05

## 목표

search-only test의 search-plus-summary recovery branch에서 readiness gate를 `response-box` 대신 `response-text` 직접 참조로 변경하여 full-suite 재현성을 안정화합니다.

## 원인 분석

- 기존 gate: `response-box`에 `[모의 요약]` 포함 확인 → `response-box`는 많은 자식 요소를 포함한 큰 컨테이너
- `response-box`의 `toContainText`는 전체 DOM subtree의 textContent를 검사해야 하므로 timing sensitivity가 높음
- runtime `app/static/app.js:3153-3156`에서 `responseText.textContent`가 먼저 갱신된 후 search preview가 렌더링됨
- `response-text` element를 직접 gate로 사용하면 더 deterministic한 readiness 확인 가능

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 294-295)
  - 기존: `await expect(page.getByTestId("response-box")).toContainText("[모의 요약]");` → `await expect(page.getByTestId("response-text")).toBeVisible();`
  - 교체:
    - `await expect(page.getByTestId("response-text")).toBeVisible();` (search-only hidden → visible 복구 확인)
    - `await expect(page.getByTestId("response-text")).toContainText("[모의 요약]");` (response 텍스트 준비 확인)

## 변경하지 않은 것

- line 246의 search-only pre-preview gate
- verdict-state family, cancel family
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `make e2e-test`: **17 passed (4.9m)**

## python3 -m unittest 생략 사유

test-only Playwright stabilization 라운드이며 Python runtime/handler 코드는 수정하지 않았으므로 unit test를 생략합니다.
