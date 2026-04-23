# 2026-04-23 Controller ready/working 상태 표시 보정

## 변경 파일
- `controller/js/cozy.js`
- `controller/js/state.js`
- `e2e/tests/controller-smoke.spec.mjs`
- `work/4/23/2026-04-23-controller-ready-working-state.md`

## 사용 skill
- `e2e-smoke-triage`: 컨트롤러 화면 표시 계약 변경이라 재현 Playwright 시나리오를 먼저 추가하고 좁은 smoke부터 검증했다.
- `finalize-lite`: 변경 파일, 실행 검증, 문서 동기화 필요 여부, 남은 리스크를 마무리 점검했다.
- `work-log-closeout`: 이번 구현 라운드의 실제 변경과 검증 결과를 `/work` 노트로 남겼다.

## 변경 이유
- `controller/index.html`은 `/controller-assets/js/cozy.js`를 로드하고, 기존 `cozy.js`는 runtime lane snapshot의 `state`를 그대로 사용자 표시 상태로 사용했다.
- 이 때문에 `active_round.state=VERIFYING`으로 검증 라운드가 진행 중이어도 해당 verify owner lane snapshot이 `ready`이면 canvas/modal/debug 표시가 `READY`로 보일 수 있었다.
- `turn_state.state=IDLE`이 같이 내려오는 경우 sidebar `Current Round`도 실제 진행 중인 `active_round.state`보다 IDLE을 우선할 수 있었다.

## 핵심 변경
- `cozy.js`에 `liveRoundState()`를 추가해 live runtime 표시에서는 `active_round.state`가 `IDLE`이 아닐 때 이를 우선하도록 했다.
- `active_round.state`가 `VERIFYING` 또는 `RECEIPT_PENDING`이면 현재 `role_owners.verify` lane을 활성 작업 lane으로 해석한다.
- 활성 작업 lane의 raw state가 `ready` 또는 `idle`이면 사용자 표시용 state를 `working`으로 보정한다.
- split-module 쪽 `controller/js/state.js`의 presentation 라운드 상태 계산도 같은 우선순위로 맞췄다.
- `controller-smoke.spec.mjs`에 `VERIFYING + turn_state IDLE + verify owner lane ready` 재현 테스트를 추가해 canvas/debug state, sidebar Round, modal state가 `WORKING`/`VERIFYING`으로 보이는지 확인한다.

## 검증
- `npx playwright test controller-smoke.spec.mjs --config=playwright.controller.config.mjs --grep "active verify owner"` (`workdir=e2e`) → 1 passed.
- `node --check controller/js/cozy.js` → 통과.
- `node --check controller/js/state.js` → 통과.
- `npx playwright test controller-smoke.spec.mjs --config=playwright.controller.config.mjs` (`workdir=e2e`) → 14 passed.
- `git diff --check -- controller/js/cozy.js controller/js/state.js e2e/tests/controller-smoke.spec.mjs` → 통과.

## 남은 리스크
- 전체 앱 Playwright 묶음이나 frontend `tsc`는 실행하지 않았다. 이번 변경은 controller office 표시 로직과 해당 smoke 묶음에 한정했다.
- `controller/js/agents.js`의 raw lane 적용 함수는 현재 `controller/index.html`이 로드하는 경로가 아니라서 이번 표시 보정 대상에 포함하지 않았다.
- `app/frontend/src/api/client.ts`, `app/frontend/src/components/PreferencePanel.tsx`, `verify/4/23/2026-04-23-milestone12-axis3-trace-quality-scoring.md`, `work/4/23/2026-04-23-milestone13-axis5b-preference-panel.md`는 이번 라운드 전부터 dirty/untracked 상태였고 수정하지 않았다.
