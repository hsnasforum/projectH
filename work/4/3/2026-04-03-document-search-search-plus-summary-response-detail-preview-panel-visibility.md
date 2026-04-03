# 2026-04-03 document-search search-plus-summary response-detail preview-panel visibility

**범위**: search-plus-summary response detail box에서도 `#response-search-preview` panel을 보이게 함

---

## 변경 파일

- `app/static/app.js` — `renderResponseSearchPreview` 함수: `isSearchOnly` 조건을 `hasResults`와 분리하여, search_results가 있으면 항상 preview panel을 보이고 search-only일 때만 body text를 숨기도록 변경
- `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오에 response detail `#response-search-preview` visible, item count 2, `response-text` visible(summary body 유지) assertion 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

response payload는 search-only와 search-plus-summary 모두 `search_results`를 carry하고, response detail box에는 전용 `#response-search-preview` surface가 이미 있지만, 기존 `renderResponseSearchPreview()`는 search-only일 때만 preview를 보여줌. search-plus-summary에서도 검색 결과 preview를 보여주면 사용자가 summary body와 함께 원본 검색 결과를 한눈에 확인할 수 있음.

---

## 핵심 변경

1. `app/static/app.js` — `renderResponseSearchPreview`:
   - `hasResults` (search_results가 있는 모든 경우) → preview panel 보임
   - `isSearchOnly` (search_results + body가 raw 검색 결과) → body text 숨김 + copy 버튼 숨김 (기존 동작 유지)
   - search-plus-summary → preview panel + body text 둘 다 보임
2. `e2e/tests/web-smoke.spec.mjs` — folder-search 시나리오에 response detail box assertion 3건 추가

---

## 검증

- `make e2e-test` — 17 passed
- `python3 -m unittest -v tests.test_web_app` — 187 passed
- `git diff --check -- app/static/app.js e2e/tests/web-smoke.spec.mjs` — 통과

---

## 남은 리스크

- search-plus-summary response detail에서 preview panel과 summary body가 동시에 보이므로 UI가 길어질 수 있음 — 의도된 동작
- search-only의 body-hidden + copy-button-hidden 동작은 변경 없음
- docs truth-sync는 다음 슬라이스에서 처리 가능
