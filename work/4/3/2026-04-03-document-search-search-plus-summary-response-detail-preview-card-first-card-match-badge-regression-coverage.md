# 2026-04-03 document-search search-plus-summary response-detail preview-card first-card match-badge regression coverage

**범위**: folder-search(search-plus-summary) response detail first preview card의 `파일명 일치` match badge 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오에서 response detail `#response-search-preview .search-preview-match` first에 "파일명 일치" 포함 assertion 1건 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

folder-search response detail preview panel의 first card는 filename과 tooltip까지 잠갔지만, match badge는 직접 잠그지 않았음.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오:
   - `page.locator("#response-search-preview .search-preview-match").first()` → `toContainText("파일명 일치")`

---

## 검증

- `make e2e-test` — 17 passed
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- `python3 -m unittest -v tests.test_web_app` — 미실행 (server 로직 변경 없음)

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- response detail first card filename/tooltip/badge 잠김. snippet 및 second card는 별도 슬라이스 대상.
- Codex 파이프라인이 preview-card property를 card별/panel별로 개별 슬라이스로 생성하는 패턴이 반복 중. 이 granularity가 적절한지 operator 검토 권장.
