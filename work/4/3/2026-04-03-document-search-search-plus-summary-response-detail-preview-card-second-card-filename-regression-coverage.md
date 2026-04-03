# 2026-04-03 document-search search-plus-summary response-detail preview-card second-card filename regression coverage

**범위**: folder-search(search-plus-summary) response detail second preview card의 filename 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오에서 response detail `#response-search-preview .search-preview-name` second에 "memo.md" 포함 assertion 1건 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

response detail first card의 전 property(filename/tooltip/badge/snippet)는 잠겼지만, second card는 item count로 존재만 간접 확인. second card identity를 먼저 고정해야 후속 tooltip/badge/snippet 검증이 의미 있음.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오:
   - `page.locator("#response-search-preview .search-preview-name").nth(1)` → `toContainText("memo.md")`

---

## 검증

- `make e2e-test` — 17 passed
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- `python3 -m unittest -v tests.test_web_app` — 미실행 (server 로직 변경 없음)

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- response detail second card filename 잠김. tooltip/badge/snippet은 별도 슬라이스 대상.
