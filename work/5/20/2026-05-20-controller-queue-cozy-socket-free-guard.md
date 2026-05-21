# 2026-05-20 controller queue cozy socket-free guard

## 변경 파일

- `tests/test_controller_queue_presentation.py`
- `work/5/20/2026-05-20-controller-queue-cozy-socket-free-guard.md`

## 사용 skill

- `e2e-smoke-triage`: controller Playwright가 local socket 권한으로 environment-held인 상태에서, 같은 browser contract를 소켓 없이 검증하는 범위로 좁히기 위해 사용했습니다.
- `finalize-lite`: 구현 라운드 종료 전 실제 검증 결과, 문서 동기화 필요성, 남은 리스크를 정리하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실행한 검사, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- `#2037`에서 browser-level controller smoke scenario를 추가했지만, 현재 환경에서는 controller webServer socket 생성이 `PermissionError: [Errno 1] Operation not permitted`로 막혀 Playwright 본문을 실행할 수 없었습니다.
- `controller/js/state.js`는 payload-level Queue guard가 있었지만, 실제 browser-loaded `controller/js/cozy.js`의 중복 Queue presentation helper가 같은 의미를 유지하는지 소켓 없이 검증하는 보호막은 없었습니다.

## 핵심 변경

- 기존 `ControllerQueuePresentationTests`에 Node 실행 공통 helper `_run_node_script()`를 추가했습니다.
- 새 `test_cozy_queue_presentation_matches_runtime_payloads_without_socket`를 추가했습니다.
- 테스트는 `controller/js/cozy.js` 원문에서 `currentTurnState()`, `liveRoundState()`, `isSuppressedOperatorCandidate()`, `isNoQueuedPipelineTask()`, `pipelineQueuePresentation()`, `getPresentation()`을 추출해 Node에서 평가합니다.
- 정상 live idle, active implement control, active verify round, `recovering`, `needs_operator` payload의 `noQueuedPipelineTask`, `pipelineQueueStatus`, `pipelineQueueClass`를 검증합니다.
- controller server, socket bind, Playwright, live runtime state, dispatch, approval, publication 동작은 사용하거나 변경하지 않았습니다.

## 검증

- `python3 -m py_compile tests/test_controller_queue_presentation.py`
  - 결과: PASS.
- `python3 -m unittest -v tests.test_controller_queue_presentation`
  - 결과: PASS. 2개 테스트가 통과했습니다.
- `git diff --check -- tests/test_controller_queue_presentation.py`
  - 결과: PASS.
- `git diff --check -- tests/test_controller_queue_presentation.py work/5/20/2026-05-20-controller-queue-cozy-socket-free-guard.md`
  - 결과: PASS.
- `node --check controller/js/cozy.js`
  - 결과: PASS.
- `node --input-type=module --check < controller/js/state.js`
  - 결과: PASS.
- `node --check e2e/tests/controller-smoke.spec.mjs`
  - 결과: PASS.

## 남은 리스크

- Playwright, controller full smoke, broad e2e, 전체 unittest, long soak는 실행하지 않았습니다. 현재 Playwright 실행 실패는 `local_socket_guard_auto_held`로 이미 `/verify`에 기록되어 있으며, 이번 slice는 소켓-비의존 behavior guard 추가로 제한했습니다.
- `cozy.js` 함수 원문을 추출해 평가하는 테스트는 helper 이름과 함수 구조가 크게 바뀌면 함께 갱신해야 합니다. 대신 별도 네트워크/DOM/socket hook 없이 현재 중복 helper drift를 잡습니다.
- `controller/js/cozy.js`와 `controller/js/state.js`의 helper 중복은 이번 slice에서 정리하지 않았습니다.
- 제품 문서는 수정하지 않았습니다. shipped behavior 확장이 아니라 controller Queue 표시의 회귀 보호 추가로 판단했습니다.
- worktree에는 이번 라운드 이전부터 있던 `controller/js/cozy.js`, `controller/js/state.js`, `e2e/tests/controller-smoke.spec.mjs` 등 다른 dirty 변경과 미추적 `/work`·`/verify` 파일들이 남아 있습니다. 이번 라운드는 위 변경 파일만 다뤘습니다.
- commit, push, PR, merge, release는 실행하지 않았습니다.
