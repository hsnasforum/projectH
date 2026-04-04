# streaming-cancel cancel-request enabled-gate reproducibility stabilization

날짜: 2026-04-04

## 목표

full-suite에서 간헐 재발하던 streaming cancel test의 pre-click readiness gate를 enabled-state 기준으로 강화합니다.

## 원인 분석

- 이전 라운드에서 phase-title gate (`not.toHaveText("파일 요약 생성 중")`)를 추가했으나, full-suite에서 여전히 간헐 실패
- cancel 버튼의 visible/enabled 분리:
  - visible: `state.isBusy` (startProgress에서 즉시 true)
  - enabled: `state.isBusy && state.currentRequestId && !state.cancelRequested`
- `state.currentRequestId`는 `submitStreamPayload` 진입 시 설정됨 (fetch 시작 직전)
- `toBeVisible()` 만으로는 `currentRequestId` 미설정 상태에서 click이 가능 → cancel POST에 유효한 request ID 없음

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 911)
  - 기존: `toBeVisible()`
  - 교체: `toBeEnabled()`
  - `toBeEnabled()`는 Playwright에서 visible + not disabled를 모두 확인
  - cancel 버튼이 enabled = `currentRequestId` 설정됨 = stream 요청 시작됨 보장

## 변경하지 않은 것

- line 912의 phase-title gate (유지)
- line 915의 success notice assertion (유지)
- runtime cancel 로직 (`app/static/app.js`, `app/handlers/chat.py`)
- verdict-state family, aggregate, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `npx playwright test -g '스트리밍 중 취소 버튼이 동작합니다' --repeat-each=3`: **3 passed (14.6s)**
- `make e2e-test`: **17 passed (4.3m)**

## python3 -m unittest 생략 사유

test-only 변경이며 Python runtime/handler 코드는 수정하지 않았으므로 unit test를 생략합니다.
