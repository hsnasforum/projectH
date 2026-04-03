# 2026-04-03 document-search search-plus-summary response-detail preview-card first-card full-path-tooltip regression coverage

**범위**: folder-search(search-plus-summary) response detail first preview card의 full-path tooltip 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오에서 response detail `#response-search-preview .search-preview-name` first에 `title` attribute가 `/budget-plan.md`로 끝나는지 assertion 1건 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

folder-search response detail preview panel의 first card는 filename까지 잠갔지만, full-path tooltip은 직접 잠그지 않았음. 구현은 모든 card에 `nameEl.title = sr.path || ""`를 설정하므로 이 path도 shipped contract이면서 regression coverage가 없었음.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오:
   - `page.locator("#response-search-preview .search-preview-name").first()` → `toHaveAttribute("title", /.*\/budget-plan\.md$/)`

---

## 검증

- `make e2e-test` — 17 passed
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- `python3 -m unittest -v tests.test_web_app` — 미실행 (server 로직 변경 없음)

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- response detail first card filename/tooltip 잠김. badge/snippet 및 second card는 별도 슬라이스 대상.
