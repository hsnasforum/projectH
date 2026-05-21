# 2026-05-20 controller client source truth guard 검증

## 검증 대상
- `work/5/20/2026-05-20-controller-client-source-truth-guard.md`
- `tests/test_controller_server.py`의 `ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only`
- `controller/index.html`
- `controller/js/cozy.js`
- `controller/js/panel.js`
- `controller/js/zones.js`

## 변경 파일
- 없음. 이 기록은 검증 노트 추가만 수행했다.

## 실행한 확인
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 44 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/ verify/5/20/`
  - 통과.

## 판단
- 최신 `/work`의 변경 주장은 현재 코드와 일치한다.
- `test_controller_html_polls_runtime_api_only`는 `controller/js/zones.js`를 추가로 읽고, `controller/index.html`이 `/controller-assets/js/queue-presentation.js`를 `/controller-assets/js/cozy.js`보다 먼저 직접 로드하는지 확인한다.
- 같은 test는 `controller/index.html`이 `panel.js`, `zones.js`, `state.js`, `config.js`, `agents.js`, `canvas.js`, `sidebar.js`를 직접 script로 로드하지 않는지 확인한다.
- `cozy.js` action button 및 modal send-input POST/JSON assertions는 shipped controller shell source contract로 남아 있다.
- `zones.js`가 `./panel.js`를 import하고, `panel.js`의 `/api/runtime/send-input` JSON POST assertions는 module-side panel source contract로 구분되어 있다.
- `controller/index.html`, `controller/js/cozy.js`, `controller/js/panel.js`, `controller/js/zones.js`, `controller/server.py` 생산 코드는 이번 구현 라운드에서 수정되지 않았다.
- 이번 verify 지시의 `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state=RUNNING`, `automation_health=recovering`, `automation_next_action=retrying`, active control `.pipeline/implement_handoff.md#2054`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`로 주어졌다. 따라서 lane-local `status --json`, `doctor --json`, `tmux` 명령은 런타임 생존성 판단에 사용하지 않았다.

## 남은 확인
- Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 이번 work 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 `local_socket_guard_auto_held` 상태가 남아 있다. 이번 검증은 controller-smoke pass, full-smoke pass, release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 verify에서는 되돌리지 않았다.

## 다음 control 판단
- `COUNCIL_DECISION: implement`
- `REASON_CODE: controller_source_contract_test_split`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2055`
- `EVIDENCE: work/5/20/2026-05-20-controller-client-source-truth-guard.md`, `verify/5/20/2026-05-20-controller-client-source-truth-guard.md`, `tests/test_controller_server.py`, `controller/index.html`, `controller/js/cozy.js`, `controller/js/panel.js`, `controller/js/zones.js`
- `REJECTED: operator_request` - 실제 runtime action 실행, release, publication, auth/credential, destructive action, approval/truth-sync repair가 아니며 socket-free test organization/source-contract guard라 operator-only boundary가 아니다.
- `REJECTED: advisory_request` - advisory가 비활성화되어 있고, 현재 `/work`, `/verify`, 테스트 코드 증거만으로 다음 안전한 local slice를 결정할 수 있다.
- `REJECTED: more_route_microguard` - 최근 같은 controller family에서 route/source guard가 여러 차례 이어졌고, 현재 더 큰 리스크는 `test_controller_html_polls_runtime_api_only`가 script ownership, endpoint presence, action request shape, module-side panel truth, queue presentation, visual source markers를 한 test에 섞고 있어 실패 원인과 shipped/module-side 계약 경계가 흐려질 수 있다는 점이다.
- 다음 안전한 local slice는 `tests/test_controller_server.py` 안에서 `test_controller_html_polls_runtime_api_only`의 기존 assertions를 잃지 않고 source-contract test를 몇 개의 목적별 test로 나누는 것이다. 생산 코드는 건드리지 않고, shipped shell script ownership/order, runtime action request-shape, module-side panel import/request-shape, 나머지 visual/source markers를 분리해 이후 drift가 더 정확히 드러나게 한다.
