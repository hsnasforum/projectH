# 2026-04-03 document-search search-only transcript preview-card first-card snippet-text regression coverage

**범위**: search-only transcript first card의 snippet text content 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오에서 transcript panel first card `.search-preview-snippet` first에 "budget-plan" 텍스트 포함 assertion 1건 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

search-only transcript preview panel의 first-card snippet은 `toBeVisible()`까지만 잠기고 실제 text content는 잠기지 않았음. second-card는 이미 `toContainText("budget")`으로 잠겨 있었고, 이번 라운드로 search-only transcript first-card도 동일 수준으로 잠김. 이로써 search-plus-summary와 search-only 양쪽 모두 response detail과 transcript의 both cards × snippet text가 전부 direct assertion으로 닫힘.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오 transcript panel:
   - `lastAssistant.locator(".search-preview-snippet").first()` → `toContainText("budget-plan")` assertion 추가 (line 276)

---

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- `make e2e-test` — 17 passed (2.0m)
- `python3 -m unittest -v tests.test_web_app` — 미실행 (server 로직 변경 없음)

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- docs 동기화 불필요 (wording이 이미 "snippet visibility"로 포괄)
- preview-card snippet text direct assertion family가 이제 전부 닫힘:
  - search-plus-summary response detail: first-card ✓, second-card ✓
  - search-plus-summary transcript: first-card ✓, second-card ✓
  - search-only response detail: first-card ✓, second-card ✓
  - search-only transcript: first-card ✓, second-card ✓
- 다음 슬라이스 후보는 preview-card snippet text family 바깥으로 이동 (tooltip/badge/item-count 등).
