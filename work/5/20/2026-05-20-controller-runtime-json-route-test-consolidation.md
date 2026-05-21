# 2026-05-20 controller runtime json route test consolidation

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-runtime-json-route-test-consolidation.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2068`이 non-send-input runtime JSON route test들의 반복 setup/assertion을 production behavior 변경 없이 줄이라고 지시했다.
- send-input route helper 정리 이후에도 `/api/runtime/status`, `/api/runtime/monitor-snapshot`, `/api/runtime/agent-inspector`, `/api/runtime/capture-tail`, `/api/runtime/start`, `/api/runtime/stop`, `/api/runtime/restart` 테스트가 mock setup, route 실행, JSON 응답 assertion을 반복하고 있었다.

## 핵심 변경
- `ControllerAssetResolutionTests`에 `_assert_runtime_get_json_route(...)` helper를 추가해 GET runtime JSON route의 mock return, route 실행, JSON 응답 assertion 반복을 줄였다.
- `ControllerAssetResolutionTests`에 `_assert_runtime_post_json_route(...)` helper를 추가해 POST runtime action route의 mock return, route 실행, JSON 응답 assertion 반복을 줄였다.
- 각 테스트의 public test name과 covered route case는 유지했다.
- `get_runtime_status`, `runtime_monitor_snapshot`, `runtime_agent_inspector`, `runtime_capture_tail`, `pipeline_start`, `pipeline_stop`, `pipeline_restart`의 expected call assertion은 각 테스트에 그대로 남겨 route별 실패 지점을 유지했다.
- production code는 변경하지 않았다.

## 검증
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 통과. `Ran 58 tests in 0.052s`, `OK`.
- `git diff --check -- tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free controller unit test 정리에 한정했다. Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- 이전 controller route family 기록의 local socket guard 환경 제약은 해소를 주장하지 않는다. controller-smoke pass나 release readiness도 주장하지 않는다.
- 작업 트리에는 이전 controller/test/work/verify 라운드의 누적 변경과 `controller/server.py`의 기존 dirty state가 남아 있다. 이번 라운드에서 의도적으로 수정한 파일은 `tests/test_controller_server.py`와 이 `/work` closeout뿐이다.
