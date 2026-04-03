# 2026-04-03 document-search search-plus-summary response-detail preview-card first-card snippet regression coverage and docs sync

**범위**: folder-search(search-plus-summary) response detail first preview card의 snippet visibility 회귀 검증 추가 + docs truth-sync

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오에서 response detail `#response-search-preview .search-preview-snippet` first visibility assertion 1건 추가
- `README.md` — scenario 3 response detail 부분에 "and snippet visibility" 추가
- `docs/ACCEPTANCE_CRITERIA.md` — 동일 반영
- `docs/MILESTONES.md` — 동일 반영
- `docs/TASK_BACKLOG.md` — 동일 반영

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

folder-search response detail first card는 filename, tooltip, badge까지 잠갔지만, snippet visibility는 직접 잠그지 않았음. assertion 추가와 동시에 docs truth-sync도 함께 처리하여 별도 라운드 불필요.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오:
   - `page.locator("#response-search-preview .search-preview-snippet").first()` → `toBeVisible()`
2. 4개 docs — "with first-card filename, full-path tooltip, and match badge" → "with first-card filename, full-path tooltip, match badge, and snippet visibility"

---

## 검증

- `make e2e-test` — 17 passed
- `git diff --check` — 통과
- `python3 -m unittest -v tests.test_web_app` — 미실행 (server 로직 변경 없음)

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- response detail first card의 filename/tooltip/badge/snippet 전부 잠김 + docs 정합. second card는 별도 슬라이스 대상.
