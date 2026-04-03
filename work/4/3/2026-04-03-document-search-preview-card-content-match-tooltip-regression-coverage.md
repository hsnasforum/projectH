# 2026-04-03 document-search preview-card content-match tooltip regression coverage

**범위**: second preview card의 content-match full-path tooltip 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오에서 response detail + transcript 양쪽의 second card `.search-preview-name`에 `title` attribute가 `/memo.md`로 끝나는지 검증하는 assertion 추가 (2건)

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

first card의 full-path tooltip은 이전 라운드에서 잠갔지만, second card(content-match path)의 tooltip은 직접 잠그지 않았음. 구현은 모든 card에 `nameEl.title = sr.path || ""`를 설정하므로 second card tooltip도 shipped contract이면서 regression coverage가 없었음.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오:
   - response detail: second `.search-preview-name` → `toHaveAttribute("title", /.*\/memo\.md$/)`
   - transcript: 동일 1건

---

## 검증

- `make e2e-test` — 17 passed
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- docs는 이미 "full-path tooltip on preview card filenames"로 모든 card를 포괄하여 추가 동기화 불필요
- preview-card contract의 both cards × all properties(filename, tooltip, badge, snippet) 전부 잠김. same-family current-risk 닫힘.
