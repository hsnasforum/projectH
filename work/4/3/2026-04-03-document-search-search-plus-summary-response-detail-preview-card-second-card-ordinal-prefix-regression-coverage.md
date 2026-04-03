# 2026-04-03 document-search search-plus-summary response-detail preview-card second-card ordinal-prefix regression coverage

**범위**: search-plus-summary response detail second card의 ordinal prefix 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — search-plus-summary 시나리오에서 response detail panel second card `.search-preview-name` nth(1)에 "2. memo.md" ordinal prefix 포함 assertion 1건 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

search-plus-summary response detail panel의 second-card는 bare `memo.md`만 잠기고 ordinal prefix `2.`는 잠기지 않았음. first-card는 이전 라운드에서 이미 `1. budget-plan.md`로 잠겼으므로, second-card에도 동일 수준의 ordinal prefix assertion이 필요.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — search-plus-summary 시나리오 response detail panel:
   - `page.locator("#response-search-preview .search-preview-name").nth(1)` → `toContainText("2. memo.md")` assertion 추가 (line 212)

---

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- `make e2e-test` — 17 passed (2.5m)
- `python3 -m unittest -v tests.test_web_app` — 미실행 (server 로직 변경 없음)

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- docs 동기화 불필요
- search-plus-summary response detail panel의 both cards ordinal prefix가 이제 전부 잠김. search-plus-summary response detail ordinal prefix family 닫힘.
- search-plus-summary transcript panel both cards ordinal prefix 공백 남아 있음. 다음 슬라이스 후보.
