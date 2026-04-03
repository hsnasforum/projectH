# 2026-04-03 document-search search-plus-summary transcript preview-card second-card snippet-text regression coverage

**범위**: folder-search transcript second card의 snippet text content 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오에서 search-plus-summary transcript panel second card `.search-preview-snippet` nth(1)에 "budget" 텍스트 포함 assertion 1건 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

search-plus-summary transcript preview panel의 second-card snippet은 `toBeVisible()`까지만 잠기고 실제 text content는 잠기지 않았음. first-card는 이전 라운드에서 이미 `toContainText("budget-plan")`으로 잠겼고, response detail panel에서는 second-card도 이미 `toContainText("budget")`으로 잠겨 있어 transcript panel의 second-card에도 동일 수준의 content assertion이 필요. second card(memo.md)는 content match이므로 snippet에 "budget"이 포함됨.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오 search-plus-summary transcript panel:
   - `lastAssistant.locator(".search-preview-snippet").nth(1)` → `toContainText("budget")` assertion 추가 (line 230)

---

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- `make e2e-test` — 17 passed (2.0m)
- `python3 -m unittest -v tests.test_web_app` — 미실행 (server 로직 변경 없음)

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- docs 동기화 불필요 (wording이 이미 "snippet visibility"로 포괄)
- search-plus-summary transcript panel의 both cards × snippet text가 이제 전부 잠김. search-plus-summary transcript preview-card family 닫힘.
- search-only family의 first-card snippet text direct coverage 공백이 남아 있음. 다음 슬라이스 후보.
