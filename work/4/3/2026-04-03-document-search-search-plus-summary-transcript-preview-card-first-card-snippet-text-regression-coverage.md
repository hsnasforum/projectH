# 2026-04-03 document-search search-plus-summary transcript preview-card first-card snippet-text regression coverage

**범위**: folder-search transcript first card의 snippet text content 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오에서 search-plus-summary transcript panel first card `.search-preview-snippet` first에 "budget-plan" 텍스트 포함 assertion 1건 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

search-plus-summary transcript preview panel의 first-card snippet은 `toBeVisible()`까지만 잠기고 실제 text content는 잠기지 않았음. response detail panel에서는 이미 first-card `toContainText("budget-plan")`과 second-card `toContainText("budget")`으로 잠겨 있어, transcript panel의 first-card에도 동일 수준의 content assertion이 필요. first card(budget-plan.md)는 filename match이므로 snippet에 "budget-plan"이 포함됨.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오 search-plus-summary transcript panel:
   - `lastAssistant.locator(".search-preview-snippet").first()` → `toContainText("budget-plan")` assertion 추가 (line 225)

---

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- `rg -n "search-preview-snippet|budget-plan|budget|folder-search|search-preview-panel" e2e/tests/web-smoke.spec.mjs` — 올바른 위치 확인
- `make e2e-test` — 17 passed (1.9m)
- `python3 -m unittest -v tests.test_web_app` — 미실행 (server 로직 변경 없음)

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- docs 동기화 불필요 (wording이 이미 "snippet visibility"로 포괄)
- search-plus-summary transcript panel의 second-card snippet text direct assertion은 아직 없음. 다음 슬라이스 후보.
- search-only transcript/response-detail first-card snippet text direct coverage 공백도 남아 있음.
