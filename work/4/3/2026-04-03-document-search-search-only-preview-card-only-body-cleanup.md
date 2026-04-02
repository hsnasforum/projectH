# 2026-04-03 document-search search-only preview-card-only body cleanup

**범위**: pure search-only 응답에서 검색 결과 preview cards와 중복되는 body text를 transcript에서 숨기기

---

## 변경 파일

- `app/static/app.js` — transcript card 렌더링에서 search-only body 숨기기
- `app/frontend/src/components/MessageBubble.tsx` — React frontend 동일 처리
- `app/static/dist/` — Vite 빌드 산출물 갱신
- `README.md` — search-only body cleanup 반영
- `docs/PRODUCT_SPEC.md` — 동일 반영
- `docs/ACCEPTANCE_CRITERIA.md` — 동일 반영

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

pure search-only 응답에서 `message.text`는 `_format_search_results()`가 생성한 "검색 결과:" 텍스트 목록이고, `message.search_results`는 동일 데이터의 구조화된 preview cards. transcript에서 둘 다 렌더링되어 같은 정보가 중복 노출됨. preview cards가 더 나은 UX(파일명, 일치 방식 뱃지, snippet)를 제공하므로 cards를 primary surface로 유지하고 중복 body text는 숨기는 처리.

---

## 핵심 변경

1. `app/static/app.js` — transcript card 생성 시 `message.search_results` 존재 + `message.text`가 "검색 결과:"로 시작하면 `<pre>body</pre>` 렌더링 생략. search+summary 응답은 영향 없음.
2. `app/frontend/src/components/MessageBubble.tsx` — `isSearchOnly` computed variable 추가, 해당 시 markdown body 렌더링 생략.
3. docs 3개 — "below the text body" 표현 제거, search-only body cleanup 동작 명시.

---

## 검증

- `python3 -m unittest -v tests.test_web_app` — **187 tests OK**
- `make e2e-test` — **16 passed** (기존 folder-search 포함 전체 통과)
- `git diff --check -- app/static/app.js app/frontend/src/components/MessageBubble.tsx README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md` — 통과
- `npx tsc --noEmit` — 기존 에러만 (Sidebar.tsx, useChat.ts, main.tsx — 제 변경과 무관)
- `npx vite build` — 성공

---

## 남은 리스크

- 분기 기준은 `message.text.startsWith("검색 결과:")`로, `_format_search_results()`의 출력 형식에 의존. 백엔드에서 해당 함수의 첫 줄을 바꾸면 분기가 깨질 수 있으나, 현재 코드에서 안정적.
- response detail box(상단 응답 도구)에는 search preview cards가 없어 body text를 유지. detail box에도 preview cards를 추가하려면 별도 슬라이스가 필요.
- search+summary, approval-request, approved-save 경로는 body text가 summary로서 고유 가치를 가지므로 영향 없음.
