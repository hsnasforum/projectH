# 2026-04-03 document-search response-detail body-visibility reset after search-only

**범위**: search-only → search-plus-summary 전환 시 response body visibility 복구 버그 수정 + 전환 regression coverage

---

## 변경 파일

- `app/static/app.js` — `renderResponseSearchPreview`에서 `hasResults && !isSearchOnly`일 때 `responseText.hidden = false`를 명시적으로 설정
- `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오 끝에서 같은 세션에서 search-plus-summary 전환 후 `response-text` visible + `response-search-preview` visible assertion 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

직전 라운드에서 `hasResults`면 preview panel을 보이게 했지만, search-only가 `responseText.hidden = true`를 설정한 뒤 search-plus-summary로 전환되면 `responseText.hidden`을 복구하는 코드가 없었음. fresh session happy path만 테스트했기 때문에 이 상태 전이 회귀를 놓침.

---

## 핵심 변경

1. `app/static/app.js` — `renderResponseSearchPreview`:
   - `hasResults && !isSearchOnly` branch에 `responseText.hidden = false` 추가
2. `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오 끝에서:
   - `#search-only` uncheck → submit → `[모의 요약]` 확인
   - `response-text` visible + `response-search-preview` visible 확인

---

## 검증

- `make e2e-test` — 17 passed
- `python3 -m unittest -v tests.test_web_app` — 187 passed
- `git diff --check -- app/static/app.js e2e/tests/web-smoke.spec.mjs` — 통과

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음 (기존 시나리오 안에 전환 regression 추가)
- docs truth-sync는 다음 슬라이스 대상
