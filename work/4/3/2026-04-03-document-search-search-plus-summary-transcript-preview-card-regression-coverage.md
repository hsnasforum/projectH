# 2026-04-03 document-search search-plus-summary transcript preview-card regression coverage

**범위**: folder-search(search-plus-summary) 시나리오에서 transcript preview panel contract 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오에서 transcript last assistant의 `.search-preview-panel` visible, `.search-preview-item` count(2), first card filename(`budget-plan.md`), first card badge(`파일명 일치`) assertion 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

root docs는 search-only와 search-plus-summary 양쪽 모두 structured preview panel을 포함한다고 적지만, browser smoke의 folder-search 시나리오는 quick-meta/transcript meta와 `selected-text`만 확인하고 transcript preview panel 자체는 직접 잠그지 않았음. search-plus-summary transcript preview panel이 shipped contract이면서 regression coverage가 없었음.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오 끝에:
   - `lastAssistant.locator(".search-preview-panel")` → visible
   - `.search-preview-item` → count 2
   - `.search-preview-name` first → "budget-plan.md" 포함
   - `.search-preview-match` first → "파일명 일치" 포함

---

## 검증

- `make e2e-test` — 17 passed
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음 (기존 시나리오 안에 assertion 추가)
- docs는 이미 both-path preview panel을 기술하여 추가 동기화 불필요
- document-search preview-card contract의 search-only + search-plus-summary 양쪽 transcript regression coverage 확보됨. same-family current-risk 닫힘.
