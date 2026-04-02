# 2026-04-03 document-search search-only response-box preview-card expansion

**범위**: search-only 응답의 response detail box에 search_results preview cards를 노출하고 raw text body를 숨기기

---

## 변경 파일

- `app/templates/index.html` — `#response-search-preview` 컨테이너 div 추가
- `app/static/app.js` — `renderResponseSearchPreview()` 함수 추가, `renderResult()`와 `renderSession()` 양쪽에서 호출
- `e2e/tests/web-smoke.spec.mjs` — search-only E2E smoke assertion을 response detail box preview cards 검증으로 갱신
- `README.md` — "transcript" → "transcript and response detail box" 반영
- `docs/PRODUCT_SPEC.md` — 동일 반영
- `docs/ACCEPTANCE_CRITERIA.md` — 동일 반영

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

이전 라운드에서 transcript의 search-only body-hiding은 구현됐지만, response detail box(상단 응답 도구)는 여전히 raw "검색 결과:" 텍스트만 보여 snippet preview surface가 없었음. transcript과 동일한 preview cards를 response detail box에도 노출하여 search-only 결과의 즉시 가독성을 개선.

---

## 핵심 변경

1. `app/templates/index.html` — `<pre id="response-text">` 바로 뒤에 `<div id="response-search-preview" class="search-preview-panel" hidden>` 추가.
2. `app/static/app.js` — `renderResponseSearchPreview(searchResults, textValue)`: search-only일 때 `responseText`를 숨기고 preview cards(filename, match badge, snippet)를 렌더링. 아닐 때는 responseText 복원, preview panel 숨김.
3. `renderResult()`와 `renderSession()` 양쪽에서 호출하여 fresh response와 session reload 모두 대응.
4. E2E smoke — response detail box에서 `#response-search-preview` visible + 2 items + 파일명 확인, `#response-text` hidden 확인으로 갱신.
5. docs 3개 — "transcript" 한정 → "transcript and response detail box" 반영.

---

## 검증

- `make e2e-test` — **17 passed** (search-only smoke 포함 전체 통과)
- `python3 -m unittest tests.test_web_app` — **187 tests OK**
- `git diff --check` — 통과

---

## 남은 리스크

- search+summary 응답에서는 preview panel이 숨겨지고 summary text body가 보이는 기존 동작 유지. search+summary E2E smoke(folder-search)가 이를 잠금.
- `본문 복사` 버튼은 search-only에서도 hidden responseText의 textContent를 복사 — UX 개선 여지가 있으나 기능상 동작함.
- React frontend `MessageBubble.tsx`는 이미 이전 라운드에서 body-hiding이 구현돼 있고, response detail box는 React와 별도 렌더링 경로이므로 추가 변경 불필요.
