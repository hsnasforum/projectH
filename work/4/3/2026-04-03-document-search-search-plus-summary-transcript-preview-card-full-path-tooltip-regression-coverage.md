# 2026-04-03 document-search search-plus-summary transcript preview-card full-path-tooltip regression coverage

**범위**: folder-search(search-plus-summary) transcript first preview card의 full-path tooltip 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오에서 transcript first card `.search-preview-name`에 `title` attribute가 `/budget-plan.md`로 끝나는지 검증하는 assertion 1건 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

folder-search 시나리오는 transcript preview panel visible, item count, first card filename, badge까지 잠갔지만, first card의 full-path tooltip은 직접 잠그지 않았음. 구현은 모든 card에 `nameEl.title = sr.path || ""`를 설정하므로 이 path도 shipped contract이면서 regression coverage가 없었음.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오:
   - `lastAssistant.locator(".search-preview-name").first()` → `toHaveAttribute("title", /.*\/budget-plan\.md$/)`

---

## 검증

- `make e2e-test` — 17 passed
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- docs는 지시에 따라 이번 슬라이스에서 건드리지 않음
- folder-search transcript first card의 filename, tooltip, badge 잠김. snippet과 second card는 아직 잠기지 않았으나 별도 슬라이스 대상.
