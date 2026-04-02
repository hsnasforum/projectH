# 2026-04-03 document-search search-only transcript hidden-body browser regression

**범위**: pure search-only transcript hidden-body contract를 직접 잠그는 Playwright smoke 1건 추가 + `_assistant_message()` search_results 저장 gap 수정

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — "검색만 응답은 transcript에서 preview cards만 보이고 본문 텍스트는 숨겨집니다" E2E smoke 1건 추가
- `core/agent_loop.py` — `_assistant_message()`에 `search_results` session 저장 2줄 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

이전 라운드(`work/4/3/2026-04-03-document-search-search-only-preview-card-only-body-cleanup.md`)에서 transcript body-hiding 코드를 `app.js`에 추가했지만, `_assistant_message()`가 `search_results`를 session message에 저장하지 않아 transcript에서 `message.search_results`가 항상 `undefined`였음. 이로 인해:
1. transcript preview cards가 절대 렌더링되지 않았음
2. body-hiding 분기(`isSearchOnly`)도 절대 true가 되지 않았음
3. 즉 이전 라운드의 transcript body-hiding이 실제로 동작하지 않는 상태였음

`_assistant_message()`에 `search_results` 저장을 추가하여 이전 라운드의 변경이 실제로 동작하게 한 뒤, E2E smoke로 직접 잠금.

---

## 핵심 변경

1. `core/agent_loop.py:_assistant_message()` — `response.search_results`가 있을 때 session message dict에 `search_results` 포함. 기존 `evidence`, `summary_chunks` 등과 동일한 패턴.
2. `e2e/tests/web-smoke.spec.mjs` — search-only E2E smoke:
   - 검색 모드 + "검색만" 체크박스 활성화 + 폴더 선택 + 쿼리 입력 + 제출
   - response detail box에 "검색 결과:" text 확인
   - transcript에 `.search-preview-panel` visible, `.search-preview-item` 2개 확인
   - transcript에 `<pre>` body 0개 확인 (search-only body hidden)

---

## 검증

- `make e2e-test` — **17 passed** (기존 16 + 신규 1, 기존 folder-search smoke 포함 전체 통과)
- `python3 -m py_compile core/agent_loop.py` — 통과
- `python3 -m unittest tests.test_web_app` — **187 tests OK**
- `git diff --check -- e2e/tests/web-smoke.spec.mjs core/agent_loop.py` — 통과

---

## 남은 리스크

- `_assistant_message()`의 `search_results` 저장이 이제 추가됐으므로, session JSON 파일 크기가 search-only 응답에서 약간 증가. 기존 `evidence`, `summary_chunks`와 동일한 패턴이라 schema 호환성 문제 없음.
- search+summary 경로도 `search_results`를 session에 저장하게 됨 — 기존 E2E folder-search smoke(17개 중 3번)가 search+summary path에서 여전히 통과하므로 regression 없음.
- response detail box에는 여전히 search preview cards가 없어 "검색 결과:" text body를 유지. detail-box preview expansion은 별도 슬라이스.
