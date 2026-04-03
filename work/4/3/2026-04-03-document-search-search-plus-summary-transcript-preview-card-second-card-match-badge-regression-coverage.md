# 2026-04-03 document-search search-plus-summary transcript preview-card second-card match-badge regression coverage

**범위**: folder-search(search-plus-summary) transcript second preview card의 `내용 일치` match badge 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오에서 transcript second card `.search-preview-match`에 "내용 일치" 포함 assertion 1건 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

folder-search 시나리오의 transcript second card는 filename과 tooltip까지 잠갔지만, match badge는 직접 잠그지 않았음. `memo.md`는 content match로 분류되므로 `내용 일치` badge가 shipped contract이면서 regression coverage가 없었음.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오:
   - `lastAssistant.locator(".search-preview-match").nth(1)` → `toContainText("내용 일치")`

---

## 검증

- `make e2e-test` — 17 passed
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- folder-search transcript second card의 filename/tooltip/badge 잠김. snippet은 별도 슬라이스 대상.
