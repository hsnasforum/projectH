# streaming-cancel-success-notice reproducibility stabilization

날짜: 2026-04-04

## 목표

full-suite 기준으로 streaming cancel success notice 재현성을 안정화합니다. isolated 실행에서는 항상 통과하지만 full-suite에서는 간헐 실패하던 flake를 해결합니다.

## 원인 분석

- cancel 버튼은 `startProgress` → `setBusyControls(true)`에서 visible이 됨
- 이 시점은 SSE stream 연결 전 (클라이언트 `submitStreamPayload`의 `fetch` 호출 전)
- mock adapter의 `LOCAL_AI_MOCK_STREAM_DELAY_MS=10`에서는 전체 파이프라인이 ~1-2초 안에 완료
- full-suite 워밍업 후에는 더 빠르게 완료될 수 있음
- Playwright `toBeVisible()` 통과 후 `click()` 처리 사이에 stream이 완료되면:
  - `stopProgress()` → `state.isBusy = false`
  - `cancelCurrentRequest()` 진입 시 `state.isBusy` check에서 즉시 return
  - cancel 동작 없이 `#notice-box`가 empty hidden 상태로 남음

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 910)
  - cancel 클릭 전에 서버 phase event 도착 확인 추가:
    - `await expect(page.locator("#progress-title")).not.toHaveText("파일 요약 생성 중");`
  - 초기 progress title "파일 요약 생성 중"은 클라이언트 `buildProgressMessage`가 설정
  - 서버 phase event가 도착하면 title이 변경됨 (예: "파일 읽는 중", "대용량 문서 구간 분석 중")
  - `not.toHaveText` assertion 통과 = SSE stream 활성 + 서버 처리 진행 중 확인
  - 이 시점에서 cancel 클릭하면 서버의 `_active_stream_requests`에 여전히 등록되어 있어 취소 가능

## 변경하지 않은 것

- runtime cancel 로직 (`app/static/app.js`, `app/handlers/chat.py`)
- content-verdict family (line 352, 395)
- aggregate/claim-coverage/history-card 시나리오
- docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs app/static/app.js app/handlers/chat.py`: 통과
- `npx playwright test -g '스트리밍 중 취소 버튼이 동작합니다' --repeat-each=3`: **3 passed (17.2s)**
- `make e2e-test`: **17 passed (4.5m)**

## python3 -m unittest 생략 사유

test-only 변경이며 Python runtime/handler 코드는 수정하지 않았으므로 unit test를 생략합니다.

## 잔여 리스크

- mock stream delay가 극단적으로 줄어들면 (0ms 등) phase event 도착 전 stream이 완료될 수 있으나, 현재 10ms 설정에서는 재현 불가
