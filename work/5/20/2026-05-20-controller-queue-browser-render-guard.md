# 2026-05-20 controller queue browser render guard

## 변경 파일

- `e2e/tests/controller-smoke.spec.mjs`
- `work/5/20/2026-05-20-controller-queue-browser-render-guard.md`

## 사용 skill

- `e2e-smoke-triage`: controller Playwright smoke의 기존 route-stub, selector, 실행 범위를 확인하고 focused scenario로 제한하기 위해 사용했습니다.
- `finalize-lite`: 구현 라운드 종료 전 실제 검증 결과, 문서 동기화 필요성, 남은 리스크를 정리하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실행한 검사, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- `#2036`은 `controller/js/state.js`의 `PipelineState.getPresentation()` 동작을 payload 수준으로 보호했지만, 실제 browser-loaded `controller/js/cozy.js`가 sidebar `Queue` 행과 marquee에 같은 상태를 렌더링하는지는 Playwright coverage가 없었습니다.
- 이번 handoff의 목표는 정상 live idle의 `No queued pipeline task` 표시가 active control, active round, recovering, operator-needed 상태와 browser surface에서 섞이지 않도록 회귀 테스트를 추가하는 것입니다.

## 핵심 변경

- controller smoke spec에 `queueRuntimePayload()` helper를 추가해 runtime status payload fixture를 재사용하도록 했습니다.
- `expectQueuePresentation()` helper를 추가해 `#tab-content`의 `Current Round` 섹션 내 `Queue` 값, tone class, `#marquee-text`의 `Queue ...` 문구를 함께 확인합니다.
- 새 Playwright scenario `controller renders Queue presentation from runtime payloads`를 추가했습니다.
- 테스트는 `/api/runtime/status`를 stub하고 페이지를 payload별로 다시 로드해 정상 idle, active implement control, active verify round, `recovering`, `needs_operator` Queue 표시를 검증합니다.
- controller runtime, dispatch, supervisor, socket, approval, publication 동작은 변경하지 않았습니다.

## 검증

- `cd e2e && CONTROLLER_SMOKE_PORT=8782 npx playwright test --config=playwright.controller.config.mjs -g "controller renders Queue presentation" --reporter=line`
  - 결과: FAIL. Playwright webServer 시작 중 `hostname: Operation not permitted`와 `PermissionError: [Errno 1] Operation not permitted`가 발생해 controller server socket 생성 단계에서 중단되었습니다. 테스트 본문은 실행되지 않았습니다.
- `node --check e2e/tests/controller-smoke.spec.mjs`
  - 결과: PASS.
- `git diff --check -- e2e/tests/controller-smoke.spec.mjs`
  - 결과: PASS.
- `git diff --check -- e2e/tests/controller-smoke.spec.mjs work/5/20/2026-05-20-controller-queue-browser-render-guard.md`
  - 결과: PASS.
- `cd e2e && npx playwright test --config=playwright.controller.config.mjs -g "controller renders Queue presentation" --list`
  - 결과: PASS. `controller-smoke.spec.mjs:691:3 › controller office smoke › controller renders Queue presentation from runtime payloads` 1개 테스트가 검색되었습니다.

## 남은 리스크

- focused Playwright scenario는 추가됐지만, 현재 환경의 socket 권한 문제로 실제 browser execution pass는 확인하지 못했습니다. controller-smoke pass나 release readiness는 주장하지 않습니다.
- `local_socket_guard_auto_held`와 동등한 local environment-held 상태로 기록하지만, `.pipeline/operator_request.md`는 작성하지 않았습니다.
- `controller/js/cozy.js`와 `controller/js/state.js`의 helper 중복은 이번 slice에서 정리하지 않았습니다. 이번 변경은 browser-facing regression guard 추가에 한정했습니다.
- 전체 Playwright, broad e2e, 전체 unittest, long soak는 실행하지 않았습니다.
- worktree에는 이번 라운드 이전부터 있던 `controller/js/cozy.js`, `controller/js/state.js` 등 다른 dirty 변경과 미추적 `/work`·`/verify` 파일들이 남아 있습니다. 이번 라운드는 위 변경 파일만 다뤘습니다.
- commit, push, PR, merge, release는 실행하지 않았습니다.
