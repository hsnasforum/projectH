# 2026-05-20 controller runtime json route test consolidation 검증

## 검증 대상
- `work/5/20/2026-05-20-controller-runtime-json-route-test-consolidation.md`
- `tests/test_controller_server.py`의 `ControllerAssetResolutionTests` non-send-input runtime JSON route test helper 정리

## 변경 파일
- 없음
- 이 검증 단계는 코드와 테스트를 수정하지 않았고 이 `/verify` 기록만 추가했다.

## 사용 skill
- `round-handoff`: 최신 `/work` 주장을 현재 테스트 코드와 좁은 검증으로 대조하고 다음 control 전 `/verify`를 남기는 데 사용했다.
- `next-slice-triage`: 검증 truth가 맞는 상태에서 advisory/operator 없이 이어갈 수 있는 한 가지 다음 slice를 고르는 데 사용했다.

## 실행한 확인
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 통과. `Ran 58 tests in 0.042s`, `OK`.
- `git diff --check -- tests/test_controller_server.py work/5/20/ verify/5/20/`
  - 통과.
- `rg -n "_assert_runtime_get_json_route|_assert_runtime_post_json_route|test_do_get_runtime_status_route|test_do_get_monitor_snapshot_route|test_do_get_agent_inspector_route|test_do_get_capture_tail_route|test_do_post_runtime_start_route|test_do_post_runtime_stop_route|test_do_post_runtime_restart_route" tests/test_controller_server.py`
  - `_assert_runtime_get_json_route(...)`와 `_assert_runtime_post_json_route(...)`가 추가되었고, non-send-input runtime JSON route test 이름과 covered routes가 유지되는 것을 확인했다.

## 판단
- 최신 `/work`의 변경 주장은 현재 테스트 코드와 일치한다.
- `ControllerAssetResolutionTests`에는 `_assert_runtime_get_json_route(...)`가 있어 GET runtime JSON route의 mock return, route 실행, JSON 응답 assertion 반복을 줄이고 있다.
- `_assert_runtime_post_json_route(...)`는 POST runtime action route의 mock return, route 실행, JSON 응답 assertion 반복을 줄인다.
- `GET /api/runtime/status`, `GET /api/runtime/monitor-snapshot`, `GET /api/runtime/agent-inspector?agent=Codex&lines=77`, `GET /api/runtime/capture-tail?lane=Codex&lines=40`, `POST /api/runtime/start`, `POST /api/runtime/stop`, `POST /api/runtime/restart` test names와 covered routes는 유지되었다.
- `get_runtime_status`, `runtime_monitor_snapshot`, `runtime_agent_inspector`, `runtime_capture_tail`, `pipeline_start`, `pipeline_stop`, `pipeline_restart`의 `assert_called_once_with(...)` 검증도 각 test에 남아 있어 route별 backend call contract가 유지된다.
- 작업 트리에는 이전 controller route family의 `controller/server.py` 누적 변경이 남아 있다. 이번 `/work`가 주장한 최신 라운드의 의도적 변경 범위는 `tests/test_controller_server.py`와 `/work` closeout이며, 이 검증에서는 해당 범위만 대조했다.
- `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state: RUNNING`, `automation_health: recovering`, `automation_next_action: retrying`이므로 runtime liveness 판단에는 이 dispatcher surface를 authoritative로 사용했다. lane-local `status --json`, `doctor --json`, `tmux` 검사는 실행하지 않았다.

## 남은 확인과 위험
- Playwright, full controller smoke, broad e2e, runtime start/stop, long soak은 실행하지 않았다. 이번 변경은 socket-free controller unit test helper 정리에 한정되어 좁은 단위 검증이 충분하다고 판단했다.
- 이전 계열에서 기록된 local socket guard 환경 제약은 해소를 주장하지 않는다. release-ready 또는 full-smoke-pass도 주장하지 않는다.
- controller runtime route/status behavior와 socket-free route guards가 여러 라운드에 걸쳐 누적되었다. 테스트 truth는 정리되었지만, current docs가 `runtime_snapshot`, read-only status/monitor routes, fail-closed send-input validation, local socket guard 제약을 현재 behavior와 같은 수준으로 설명하는지는 아직 이 검증에서 확인하지 않았다.

## 다음 control 판단
- `COUNCIL_DECISION: implement`
- `REASON_CODE: controller_runtime_route_docs_truth_sync`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2069`
- `EVIDENCE: controller/server.py`, `tests/test_controller_server.py`, `work/5/20/2026-05-20-controller-runtime-json-route-test-consolidation.md`, `verify/5/20/2026-05-20-controller-runtime-json-route-test-consolidation.md`
- `REJECTED: operator_request` - destructive write, credential/auth, approval-record repair, truth-sync blocker that blocks local work now, external publication, merge, immediate safety stop이 아니다.
- `REJECTED: advisory_request` - `ADVISORY_ENABLED: false`이며 다음 local slice가 명확하다.
- `REJECTED: another controller route helper cleanup` - helper 정리는 send-input과 non-send-input runtime JSON route tests까지 완료되어 현재 risk reduction이 줄었다. 같은 class의 추가 helper 미화보다 누적 behavior를 docs truth와 맞추는 편이 shipped contract drift를 더 줄인다.
- 다음 safe local slice는 controller runtime route/status behavior를 현재 구현과 테스트에 맞게 docs에 bounded sync하는 것이다. 코드 변경이나 추가 route test는 포함하지 않는다.
