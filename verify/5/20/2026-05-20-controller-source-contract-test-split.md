# 2026-05-20 controller source contract test split 검증

## 검증 대상
- `work/5/20/2026-05-20-controller-source-contract-test-split.md`
- `tests/test_controller_server.py`의 `ControllerServerLaunchGateTests`
- `ControllerServerLaunchGateTests._controller_sources`
- `test_controller_shell_scripts_keep_shared_source_ownership`
- `test_controller_shell_runtime_api_source_contract`
- `test_controller_shell_action_request_shape_contract`
- `test_controller_panel_request_shape_stays_module_side`
- `test_controller_visual_source_markers_stay_available`

## 변경 파일
- 없음. 이 기록은 검증 노트 추가만 수행했다.

## 실행한 확인
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 48 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/ verify/5/20/`
  - 통과.

## 판단
- 최신 `/work`의 변경 주장은 현재 코드와 일치한다.
- `ControllerServerLaunchGateTests`에는 `_controller_sources()` helper가 추가되어 `index.html`, `office.css`, `server.py`, `cozy.js`, `panel.js`, `queue-presentation.js`, `zones.js` source 읽기를 한 곳으로 모은다.
- 기존 큰 `test_controller_html_polls_runtime_api_only`는 더 이상 남아 있지 않고, shipped shell script ownership/order, runtime API/source markers, action request shape, module-side panel source truth, visual/source markers가 5개 focused test로 분리되어 있다.
- `test_controller_shell_scripts_keep_shared_source_ownership`는 `queue-presentation.js` -> `cozy.js` 직접 script order와 module-side script 미직접로드를 확인한다.
- `test_controller_shell_runtime_api_source_contract`와 `test_controller_shell_action_request_shape_contract`는 `cozy.js`와 `server.py`의 runtime route/source marker 및 POST/JSON action wiring을 분리해 확인한다.
- `test_controller_panel_request_shape_stays_module_side`는 `zones.js`가 `./panel.js`를 import하고 `panel.js`가 module-side JSON POST request shape를 유지하는지 확인한다.
- `test_controller_visual_source_markers_stay_available`는 queue presentation, visual/source marker, CSS/layout, low-motion/local preference, delivery/event marker assertions를 보존한다.
- 생산 코드(`controller/index.html`, `controller/js/*.js`, `controller/server.py`)는 이번 구현 라운드에서 수정되지 않았다.
- 이번 verify 지시의 `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state=RUNNING`, `automation_health=recovering`, `automation_next_action=retrying`, active control `.pipeline/implement_handoff.md#2055`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`로 주어졌다. 따라서 lane-local `status --json`, `doctor --json`, `tmux` 명령은 런타임 생존성 판단에 사용하지 않았다.

## 남은 확인
- Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 이번 work 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 `local_socket_guard_auto_held` 상태가 남아 있다. 이번 검증은 controller-smoke pass, full-smoke pass, release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 verify에서는 되돌리지 않았다.

## 다음 control 판단
- `COUNCIL_DECISION: implement`
- `REASON_CODE: controller_handler_response_fixture_consolidation`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2056`
- `EVIDENCE: work/5/20/2026-05-20-controller-source-contract-test-split.md`, `verify/5/20/2026-05-20-controller-source-contract-test-split.md`, `tests/test_controller_server.py`
- `REJECTED: operator_request` - 실제 runtime action 실행, release, publication, auth/credential, destructive action, approval/truth-sync repair가 아니며 socket-free test harness consolidation이라 operator-only boundary가 아니다.
- `REJECTED: advisory_request` - advisory가 비활성화되어 있고, 현재 `/work`, `/verify`, 테스트 코드 증거만으로 다음 안전한 local slice를 결정할 수 있다.
- `REJECTED: Playwright/full-smoke rerun` - 같은 family의 local socket guard가 보류 상태이고 이번 검증은 release readiness를 주장하지 않으므로 동일한 full-smoke handoff를 재발행하지 않는다.
- 다음 안전한 local slice는 `ControllerAssetResolutionTests`의 response-capture fake handler 설정을 하나의 로컬 fixture/helper로 모으는 것이다. 현재 `_asset_response`, `_html_response`, `_json_route_response`, `_json_post_response`가 `send_response`, `send_header`, `end_headers`, `wfile` setup을 반복하고 있어, controller shell route/asset JSON response contract tests가 향후 서로 다르게 drift할 위험이 있다. 생산 코드는 건드리지 않고 테스트 harness 중복만 줄여 route/header/body assertions의 신뢰도를 유지한다.
