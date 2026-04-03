# 2026-04-03 document-search search-plus-summary transcript preview-card second-card snippet regression coverage

**범위**: folder-search(search-plus-summary) transcript second preview card의 snippet visibility 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오에서 transcript second card `.search-preview-snippet` visibility assertion 1건 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

folder-search 시나리오의 transcript second card는 filename, tooltip, badge까지 잠갔지만, snippet visibility는 직접 잠그지 않았음. 구현은 `if (sr.snippet)` 조건으로 snippet을 렌더링하므로 이 path도 shipped contract이면서 regression coverage가 없었음.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오:
   - `lastAssistant.locator(".search-preview-snippet").nth(1)` → `toBeVisible()`

---

## 검증

- `make e2e-test` — 17 passed
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- folder-search transcript both cards × all properties(filename, tooltip, badge, snippet) 전부 잠김. search-plus-summary preview-card transcript family의 same-family current-risk 닫힘.
