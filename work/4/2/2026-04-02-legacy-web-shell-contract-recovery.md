# 2026-04-02 legacy web shell contract recovery

**범위**: legacy web shell 기준 깨진 browser contract 복구
**근거 pair**: `work/4/2/2026-04-02-structural-refactor-and-feature-exposure.md` + `verify/4/2/2026-04-02-structural-refactor-and-feature-exposure-verification.md`

---

## 변경 파일

- `app/static/app.js` — response-box visibility 관리 추가 (3줄)
- `app/static/style.css` — mode-pill radio input 크기 수정 (1줄)

---

## 사용 skill

- 없음

---

## 변경 이유

4/2 세션 중 commit `34a8856` (feat: redesign frontend to modern AI chat interface)에서 `response-box`의 CSS class가 `"panel"`에서 `"assistant-card response-detail-card hidden"`으로 바뀌었으나, JS에서 이 `hidden` 클래스를 해제하는 코드가 누락되었다. 그 결과 response-box 내부의 `response-copy-text`, `response-correction-input`, `response-candidate-confirmation-box` 등 핵심 UI 컨트롤이 모두 invisible 상태가 되어 Playwright e2e smoke 16건 중 7건이 실패했다.

추가로, 같은 redesign에서 `.mode-pill input` radio 버튼의 크기가 `0×0`으로 설정되어 Playwright의 `.check()` 호출이 interactability 검사에 실패하는 문제가 2건 있었다.

---

## 핵심 변경

### 1. response-box visibility 관리 (app/static/app.js)

- `responseBox` 변수 추가: `document.getElementById("response-box")`
- `renderSession()`: 최신 assistant 메시지 유무에 따라 `showElement(responseBox, Boolean(latestAssistantMessage))` 호출
- `renderResult()`: 결과 도착 시 `showElement(responseBox, true)` 호출

이 3줄 추가로 response-box가 응답 존재 시 visible, 빈 세션에서는 hidden 상태가 된다.

### 2. mode-pill radio 크기 수정 (app/static/style.css)

- `.mode-pill input`의 `width`/`height`를 `0`에서 `1px`로 변경
- `overflow: hidden` 추가
- 시각적 차이 없이 Playwright interactability 조건 충족

---

## 검증

실제 실행한 검증:
- `python3 -m unittest -v tests.test_web_app tests.test_smoke` — **282 tests OK** (14.0s)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g '파일 요약 후 근거와 요약 구간이 보입니다'` — **passed** (7.4s)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g 'candidate confirmation path는 save support와 분리되어 기록되고 later correction으로 current state에서 사라집니다'` — **passed** (13.4s)
- `make e2e-test` — **16/16 passed** (1.5m)

---

## 남은 리스크

1. **response-box와 transcript 표시 중복**: response-box가 다시 visible이 되면서, 응답 텍스트가 transcript card와 response-box 양쪽에 표시된다. 기능적으로는 문제없지만 UX 관점에서 정리가 필요할 수 있다.
2. **SQLite backend 미수정**: verify note에서 지적된 `SQLiteTaskLogger.path` AttributeError는 이번 slice 범위 밖.
3. **React frontend 미연결**: React bundle은 여전히 서비스 경로에 연결되지 않음. 이번 slice 범위 밖.
4. **루트 문서 미동기화**: 이번 slice에서 doc sync는 제외됨.
