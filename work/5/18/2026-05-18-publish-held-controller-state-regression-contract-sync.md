# 2026-05-18 publish held controller state regression contract sync

## 변경 파일

- `tests/test_controller_server.py`
- `work/5/18/2026-05-18-publish-held-controller-state-regression-contract-sync.md`

## 사용 skill

- `e2e-smoke-triage`: Playwright controller smoke failure에서 파생된 controller state contract drift를 browser 실행 없이 unit/source inspection 범위로 좁히는 데 사용했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 non-socket 검증, 남은 browser 검증 리스크를 표준 `/work` 형식으로 기록하는 데 사용했습니다.

## 변경 이유

- `CONTROL_SEQ: 1931` handoff는 publication held 상태에서, verify가 발견한 `tests.test_controller_server.ControllerServerLaunchGateTests.test_cozy_agent_state_uses_lane_state_as_runtime_truth` 실패를 non-socket unit contract 동기화로 고치라고 지시했습니다.
- 직전 slice에서 `controller/js/cozy.js`는 `active_round.state`가 `VERIFYING` 또는 `RECEIPT_PENDING`일 때 role owner lane의 `ready` 상태를 visible `working`으로 보정하도록 바뀌었습니다.
- 기존 unit test는 `effectiveLaneState` 내부에 active-round projection이 없다는 오래된 contract를 고정하고 있어 최신 구현과 충돌했습니다.

## 핵심 변경

- `tests/test_controller_server.py`의 기존 test method 이름은 required check와 호환되도록 유지했습니다.
- test 본문은 `activeRoundLaneName` helper와 `effectiveLaneState` helper를 각각 source-inspection으로 확인하도록 갱신했습니다.
- 새 assertion은 `ACTIVE_ROUND_ROLE_BY_STATE[roundState]`, `currentRoleOwners(data)[role]`, `activeRoundLaneName(data)`, `activeRoundLane === agentName && rawState === 'ready'`, `return 'working';`를 확인합니다.
- 동시에 `turn_state`만으로 ready/idle lane을 visible `working`으로 올리지 않는 guard(`return rawState || 'off';`, `activeWorkLaneName` 미사용)는 계속 확인합니다.
- `controller/js/cozy.js`, `e2e/tests/web-smoke.spec.mjs`는 이번 slice에서 추가 수정하지 않았습니다. 직전 slice의 dirty 변경은 그대로 보존했습니다.
- commit, push, branch/PR publication, PR creation/reuse, merge, release, external publication은 수행하지 않았고 publication은 계속 held 상태입니다.

## 검증

- `python3 -m unittest -v tests.test_controller_server.ControllerServerLaunchGateTests.test_cozy_agent_state_uses_lane_state_as_runtime_truth`
  - `Ran 1 test ... OK`로 통과했습니다.
- `node --check controller/js/cozy.js`
  - 출력 없이 통과했습니다.
- `node --check e2e/tests/web-smoke.spec.mjs`
  - 출력 없이 통과했습니다.
- `git diff --check -- tests/test_controller_server.py controller/js/cozy.js e2e/tests/web-smoke.spec.mjs work/5/18/2026-05-18-publish-held-controller-state-regression-contract-sync.md`
  - 출력 없이 통과했습니다.
- `git diff --no-index --check -- /dev/null work/5/18/2026-05-18-publish-held-controller-state-regression-contract-sync.md`
  - 출력 없음. `--no-index` exit code 1은 `/dev/null`과 새 파일의 내용 차이로 발생할 수 있어 whitespace-check pass signal로 해석했습니다.
- `git status --short -- tests/test_controller_server.py controller/js/cozy.js e2e/tests/web-smoke.spec.mjs work/5/18/2026-05-18-publish-held-controller-state-regression-contract-sync.md .pipeline/implement_handoff.md .pipeline/advisory_request.md .pipeline/operator_request.md`
  - 출력: `M controller/js/cozy.js`, `M e2e/tests/web-smoke.spec.mjs`, `M tests/test_controller_server.py`, `?? work/5/18/2026-05-18-publish-held-controller-state-regression-contract-sync.md`
- Playwright, `make e2e-test`, local webServer startup, runtime start/stop/restart, socket/tmux 명령은 실행하지 않았습니다. 현재 lane의 focused Playwright path가 `local_socket_guard_auto_held`이고, 이번 handoff가 non-socket unit contract sync로 제한했기 때문입니다.

## 남은 리스크

- browser verification은 여전히 `local_socket_guard_auto_held`입니다. socket-capable 환경에서 controller focused smoke와 관련 web-smoke rerun이 필요합니다.
- 이번 slice는 unit/source-inspection contract만 동기화했으므로 full-smoke pass, release-ready, publication-ready를 주장하지 않습니다.
- `controller/js/cozy.js`와 `e2e/tests/web-smoke.spec.mjs`의 직전 dirty 변경은 유지되며, 이번 slice에서는 추가로 수정하지 않았습니다.
- dirty tree는 그대로 보존했습니다. stash apply/pop/drop/clear/branch/store/rewrite/discard는 수행하지 않았습니다.
