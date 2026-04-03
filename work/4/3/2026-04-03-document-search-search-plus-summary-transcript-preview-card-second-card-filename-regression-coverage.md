# 2026-04-03 document-search search-plus-summary transcript preview-card second-card filename regression coverage

**범위**: folder-search(search-plus-summary) transcript second preview card의 filename 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오에서 transcript second card `.search-preview-name`에 "memo.md" 포함 assertion 1건 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

folder-search 시나리오는 `.search-preview-item` count 2로 second result 존재를 간접 확인할 뿐, second card가 실제 `memo.md`인지 직접 잠그지 않았음. second card identity를 먼저 고정해야 후속 tooltip/badge/snippet 검증이 의미 있음.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오:
   - `lastAssistant.locator(".search-preview-name").nth(1)` → `toContainText("memo.md")`

---

## 검증

- `make e2e-test` — 17 passed
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- folder-search transcript second card의 filename 잠김. tooltip/badge/snippet은 별도 슬라이스 대상.
