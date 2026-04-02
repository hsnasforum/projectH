# 2026-04-03 document-search search-only preview-only response-copy button gating

**범위**: search-only preview-only 상태에서 `본문 복사` 버튼을 숨겨 hidden raw text 복사를 방지

---

## 변경 파일

- `app/static/app.js` — `renderResponseSearchPreview()`의 search-only 분기에 `showElement(responseCopyTextButton, false)` 추가
- `e2e/tests/web-smoke.spec.mjs` — search-only E2E smoke에 `response-copy-text` hidden assertion 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

이전 라운드에서 search-only response detail box는 preview cards가 primary surface가 되고 `responseText`가 hidden 됐지만, `본문 복사` 버튼은 여전히 `response.text` 존재 여부만으로 노출돼 있었음. 클릭 시 hidden raw "검색 결과:" 텍스트가 클립보드에 복사되는 misleading 동작이 남아 있었음.

---

## 핵심 변경

1. `renderResponseSearchPreview()` — `isSearchOnly` 분기에서 `showElement(responseCopyTextButton, false)` 호출. non-search-only 분기에서는 기존 동작 유지 (호출자가 별도로 copy 버튼을 show).
2. E2E smoke — `await expect(page.getByTestId("response-copy-text")).toBeHidden()` assertion 추가.

---

## 검증

- `make e2e-test` — **17 passed**
- `git diff --check -- app/static/app.js e2e/tests/web-smoke.spec.mjs` — 통과

---

## 남은 리스크

- search+summary 경로에서는 `renderResponseSearchPreview()`가 non-search-only 분기를 타므로 copy 버튼이 기존처럼 정상 노출됨. folder-search E2E smoke(3번)가 이를 잠금.
- search-only response의 "검색 결과 경로 목록만 복사하고 싶다"는 사용자 요구가 생기면 별도 copy 버튼을 추가하는 후속 슬라이스 가능하나, 현재는 misleading copy 제거가 우선.
- same-family (search-only UI cleanup) current-risk는 이번 라운드로 닫힌 상태. 다음 슬라이스는 새 quality axis로 넘어갈 수 있음.
