# 2026-04-03 document-search search-only response-detail preview-card first-card snippet-text regression coverage

**범위**: search-only response detail first card의 snippet text content 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오에서 response detail panel first card `.search-preview-snippet` first에 "budget-plan" 텍스트 포함 assertion 1건 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

search-only response detail preview panel의 first-card snippet은 `toBeVisible()`까지만 잠기고 실제 text content는 잠기지 않았음. second-card는 이미 `toContainText("budget")`으로 잠겨 있고, search-plus-summary 쪽은 response detail과 transcript 모두 both cards snippet text가 전부 닫혀 있어, search-only response detail first-card가 남은 가장 직접적인 공백이었음. first card(budget-plan.md)는 filename match이므로 snippet에 "budget-plan"이 포함됨.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오 response detail panel:
   - `page.locator("#response-search-preview .search-preview-snippet").first()` → `toContainText("budget-plan")` assertion 추가 (line 250)

---

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- `make e2e-test` — 17 passed (2.0m)
- `python3 -m unittest -v tests.test_web_app` — 미실행 (server 로직 변경 없음)

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- docs 동기화 불필요 (wording이 이미 "snippet visibility"로 포괄)
- search-only response detail panel의 both cards × snippet text가 이제 전부 잠김. search-only response detail preview-card family 닫힘.
- search-only transcript panel의 first-card snippet text direct coverage 공백이 남아 있음. 다음 슬라이스 후보.
