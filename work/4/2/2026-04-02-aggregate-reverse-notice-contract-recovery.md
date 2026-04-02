# 2026-04-02 aggregate reverse notice contract recovery

**범위**: legacy web shell — aggregate reverse 클릭 후 notice-box 계약 복구
**근거 pair**: `work/4/2/2026-04-02-legacy-web-shell-contract-recovery.md` + `verify/4/2/2026-04-02-legacy-web-shell-contract-recovery-verification.md`

---

## 변경 파일

- `app/static/app.js` — 3개 변경:
  1. `renderResult()`에서 `clearNotice()` 호출 제거
  2. `sendRequest()`/`sendFollowUpPrompt()`에서 `responseText.textContent = ""` 즉시 초기화 제거
  3. `processStreamEvent()`에서 첫 TEXT_DELTA 수신 시 responseText 초기화 (lazy clear)

---

## 사용 skill

- 없음

---

## 변경 이유

`aggregate-trigger-reverse` 클릭 후 `#notice-box`에 "검토 메모 적용이 되돌려졌습니다."가 나타나지 않는 문제. 원인은 스트리밍 요청과 aggregate action 사이의 race condition:

1. 4번째 요청 submit → `sendRequest` 시작 → `responseText.textContent = ""` (즉시 실행)
2. e2e 테스트의 `not.toContainText("[검토 메모 활성]")` 어설션이 텍스트 초기화 직후 통과 (응답 완료 전)
3. 테스트가 reverse 버튼 클릭 → reverse handler가 `renderNotice(...)` 호출
4. 그 사이 4번째 요청의 스트리밍이 완료 → `renderResult()` → `clearNotice()` → notice 제거

---

## 핵심 변경

### 1. `renderResult()`에서 `clearNotice()` 제거

`renderResult()`는 응답 렌더링 함수이며, notice 초기화는 `startProgress()`(요청 시작 시)에서 이미 처리하고 있다. `renderResult`의 중복 `clearNotice`가 aggregate action handler의 notice를 race condition으로 지우는 원인이었으므로 제거.

### 2. responseText lazy clear

`sendRequest()`/`sendFollowUpPrompt()`에서 `responseText.textContent = ""`를 즉시 실행하면, `not.toContainText` 어설션이 응답 완료 전에 통과하여 race window를 만든다. 대신 `processStreamEvent()`에서 첫 `TEXT_DELTA` 수신 시 `responseText.textContent = ""`를 실행하도록 변경. 이로써 `not.toContainText` 어설션이 실제 스트리밍 시작까지 대기.

---

## 검증

실제 실행한 검증:
- `python3 -m unittest -v tests.test_web_app tests.test_smoke` — **282 tests OK**
- targeted aggregate 테스트 10회 연속 — **10/10 passed**
- `make e2e-test` — **16/16 passed** (1.5m)

---

## 남은 리스크

1. **response-box와 transcript 표시 중복**: 이전 라운드에서 언급된 리스크 그대로 유지.
2. **SQLite backend 미수정**: 이번 slice 범위 밖.
3. **React frontend 미연결**: 이번 slice 범위 밖.
4. **루트 문서 미동기화**: 이번 slice 범위 밖.
