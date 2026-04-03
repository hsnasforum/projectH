# 2026-04-03 document-search search-plus-summary response-detail preview-card first-card snippet-text regression coverage

**범위**: folder-search response detail first card의 snippet text content 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오에서 response detail first card `.search-preview-snippet` first에 "budget-plan" 텍스트 포함 assertion 1건 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

response detail first card의 snippet은 `toBeVisible()`까지만 잠기고 실제 text content는 잠기지 않았음. second card는 이미 `toContainText("budget")`으로 잠겨 있어 first card도 동일 수준의 content assertion이 필요. first card(budget-plan.md)는 filename match이므로 snippet에 "budget-plan"이 포함됨.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오:
   - `page.locator("#response-search-preview .search-preview-snippet").first()` → `toContainText("budget-plan")`

---

## 검증

- `make e2e-test` — 17 passed
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- `python3 -m unittest -v tests.test_web_app` — 미실행 (server 로직 변경 없음)

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- docs 동기화 불필요 (wording이 이미 "snippet visibility"로 포괄)
- search-plus-summary response detail both cards × all properties + snippet text 전부 잠김. response detail preview-card family 닫힘.
