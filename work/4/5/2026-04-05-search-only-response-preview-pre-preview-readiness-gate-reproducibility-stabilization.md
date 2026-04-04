# search-only response-preview pre-preview readiness-gate reproducibility stabilization

날짜: 2026-04-05

## 목표

search-only test의 `#response-search-preview` visibility assertion 전에 response-ready gate를 추가하여 full-suite 재현성을 안정화합니다.

## 원인 분석

- search-only test는 submit 직후 `#response-search-preview`의 `toBeVisible()`을 바로 확인
- sibling search test (line 193)는 `response-box`에 `[모의 요약]` 텍스트가 나타날 때까지 대기하지만, search-only에서는 response text가 hidden
- full-suite에서는 이전 테스트의 서버 부하로 response 준비가 늦어질 수 있음
- `renderResult`의 `renderSelected` → `#selected-text`에 경로가 채워지면 response 전체가 렌더링 완료됨

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 245-246 사이)
  - 추가: `await expect(page.locator("#selected-text")).toContainText(searchFolderRelBudgetPath);`
  - `renderSelected`는 `renderResult` 안에서 호출 → `renderResponseSearchPreview`도 이미 완료된 시점

## 변경하지 않은 것

- line 294의 search-plus-summary recovery 부분
- verdict-state family, cancel family
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `--repeat-each=3` (3 workers): line 294에서 multi-worker 서버 공유 이슈로 실패 — search-only preview gate 자체는 통과
- `make e2e-test` (1 worker): **17 passed (4.6m)** — search-only test #4 포함 전부 통과

## python3 -m unittest 생략 사유

test-only Playwright stabilization 라운드이며 Python runtime/handler 코드는 수정하지 않았으므로 unit test를 생략합니다.

## 잔여 리스크

- `--repeat-each=3` (multi-worker)에서 line 294 (search-plus-summary recovery)의 `[모의 요약]` assertion 실패 — 서버 동시 접근 이슈이며 1-worker full suite에서는 재현 안 됨
