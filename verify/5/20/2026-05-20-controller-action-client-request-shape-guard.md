# 2026-05-20 controller action client request shape guard 검증

## 검증 대상
- `work/5/20/2026-05-20-controller-action-client-request-shape-guard.md`
- `tests/test_controller_server.py`의 `ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only`
- `controller/js/cozy.js`의 `apiPost()` 및 `sendModalInput()` request shape
- `controller/js/panel.js`의 `sendInput()` request shape

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
- 최신 `/work`의 변경 주장은 테스트 파일의 실제 assertions와 대체로 일치한다.
- `test_controller_html_polls_runtime_api_only`는 `controller/js/panel.js`를 추가로 읽고, `cozy.js`의 `apiPost(path)`가 `fetch(path, { method: 'POST' })`를 유지하는지 확인한다.
- 같은 test는 `cozy.js`의 start/stop/restart 버튼 wiring이 `apiPost('/api/runtime/start')`, `apiPost('/api/runtime/stop')`, `apiPost('/api/runtime/restart')`를 유지하는지 확인한다.
- 같은 test는 `cozy.js`의 `/api/runtime/send-input` 호출이 `method: 'POST'`, `Content-Type: application/json`, `JSON.stringify({ lane, text })`를 유지하는지 확인한다.
- 같은 test는 `panel.js`의 `/api/runtime/send-input` 호출이 `method: 'POST'`, `Content-Type: application/json`, `JSON.stringify({ lane: _panelLane, text })`를 유지하는지 확인한다.
- `controller/js/cozy.js`, `controller/js/panel.js`, `controller/server.py` 생산 코드는 이번 구현 라운드에서 수정되지 않았다.
- 다만 현재 `controller/index.html`은 `/controller-assets/js/queue-presentation.js`와 `/controller-assets/js/cozy.js`만 직접 로드한다. `panel.js`는 `controller/js/zones.js`가 import하는 module-side source이며, 현재 shell의 직접 script load 경로와는 분리되어 있다. 따라서 이번 guard의 `cozy.js` 부분은 현재 shipped controller shell client contract로 볼 수 있지만, `panel.js` 부분은 module-side client source contract로 구분해 기록해야 한다.
- 이번 verify 지시의 `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state=RUNNING`, `automation_health=recovering`, `automation_next_action=retrying`, active control `.pipeline/implement_handoff.md#2053`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`로 주어졌다. 따라서 lane-local `status --json`, `doctor --json`, `tmux` 명령은 런타임 생존성 판단에 사용하지 않았다.

## 남은 확인
- Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 이번 work 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 `local_socket_guard_auto_held` 상태가 남아 있다. 이번 검증은 controller-smoke pass, full-smoke pass, release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 verify에서는 되돌리지 않았다.

## 다음 control 판단
- `COUNCIL_DECISION: implement`
- `REASON_CODE: same_family_client_source_truth_guard`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2054`
- `EVIDENCE: work/5/20/2026-05-20-controller-action-client-request-shape-guard.md`, `verify/5/20/2026-05-20-controller-action-client-request-shape-guard.md`, `tests/test_controller_server.py`, `controller/index.html`, `controller/js/cozy.js`, `controller/js/panel.js`, `controller/js/zones.js`
- `REJECTED: operator_request` - 실제 runtime action 실행, release, publication, auth/credential, destructive action, approval/truth-sync repair가 아니며 socket-free test/source truth correction이라 operator-only boundary가 아니다.
- `REJECTED: advisory_request` - advisory가 비활성화되어 있고, 현재 코드/검증 증거만으로 같은 family의 보정 slice를 좁힐 수 있다.
- 다음 안전한 local slice는 source-contract test가 현재 shipped controller shell client(`cozy.js`)와 module-side panel client source(`panel.js`)를 구분하도록 보강하는 것이다. `controller/index.html`이 직접 로드하는 scripts와 `zones.js`의 `panel.js` import 관계를 test에 명시해, panel-side request-shape guard를 shipped shell behavior로 과장하지 않게 한다.
