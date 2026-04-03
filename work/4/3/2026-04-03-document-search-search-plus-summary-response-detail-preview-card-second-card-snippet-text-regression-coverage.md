# 2026-04-03 document-search search-plus-summary response-detail preview-card second-card snippet-text regression coverage

**범위**: folder-search response detail second card의 snippet text content 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오에서 response detail second card `.search-preview-snippet` nth(1)에 "budget" 텍스트 포함 assertion 1건 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

직전 라운드에서 second card의 snippet visibility까지 잠갔지만, snippet이 실제 content를 포함하는지는 직접 잠그지 않았음. search-only path는 이미 `toContainText("budget")`로 잠겨 있어 대칭성 확보가 필요했음.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오:
   - `page.locator("#response-search-preview .search-preview-snippet").nth(1)` → `toContainText("budget")`

---

## 검증

- `make e2e-test` — 17 passed
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- `python3 -m unittest -v tests.test_web_app` — 미실행 (server 로직 변경 없음)

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- docs 동기화 불필요 (wording이 이미 "snippet visibility"로 포괄)
- search-plus-summary response detail both cards × all properties(filename, tooltip, badge, snippet visibility, snippet text) 전부 잠김
