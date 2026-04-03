# 2026-04-03 document-search search-plus-summary response-detail preview-card first-card filename regression coverage

**범위**: folder-search(search-plus-summary) response detail first preview card의 filename 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오에서 response detail `#response-search-preview .search-preview-name` first에 "budget-plan.md" 포함 assertion 1건 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

folder-search 시나리오의 response detail preview panel은 visible + item count까지 잠갔지만, first card filename을 직접 잠그지 않았음. transcript path에서는 이미 잠겨 있지만 response detail path는 별도 렌더링 경로이므로 직접 확인이 필요했음.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오:
   - `page.locator("#response-search-preview .search-preview-name").first()` → `toContainText("budget-plan.md")`

---

## 검증

- `make e2e-test` — 17 passed
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- `python3 -m unittest -v tests.test_web_app` — 미실행 (server 로직 변경 없음)

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- response detail first card filename 잠김. tooltip/badge/snippet 및 second card는 별도 슬라이스 대상.
