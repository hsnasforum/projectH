# 2026-05-20 controller Queue asset resolution guard 검증

## 검증 대상
- `work/5/20/2026-05-20-controller-queue-asset-resolution-guard.md`
- `tests/test_controller_server.py`의 `ControllerAssetResolutionTests.test_resolve_real_controller_queue_js_assets`
- `controller/server.py`의 `_resolve_controller_asset()` asset root/content type 동작

## 변경 파일
- 이 검증 기록 파일 자체 외에는 없음.

## 실행한 확인
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 30 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/ verify/5/20/`
  - 통과.

## 판단
- 최신 `/work`의 변경 주장은 현재 코드와 일치한다.
- `test_resolve_real_controller_queue_js_assets`는 `_resolve_controller_asset("js/queue-presentation.js")`와 `_resolve_controller_asset("js/cozy.js")`가 실제 `controller/js/queue-presentation.js`, `controller/js/cozy.js` 경로를 반환하는지 확인한다.
- 같은 테스트는 두 asset의 content type에 `javascript`가 포함되는지도 확인한다.
- `controller/server.py`의 `_resolve_controller_asset()`는 `css/`, `js/`, 기본 `assets/` root를 분기하고 path traversal을 `relative_to(asset_root)`로 차단한 뒤 `mimetypes.guess_type()` 값을 반환한다.
- 이번 verify 지시의 `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state=RUNNING`, `automation_health=recovering`, `automation_next_action=retrying`, active control `.pipeline/implement_handoff.md#2046`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`로 주어졌다. 따라서 lane-local `status --json`, `doctor --json`, `tmux` 명령은 런타임 생존성 판단에 사용하지 않았다.

## 남은 확인
- Playwright, full controller smoke, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 이번 work 범위 밖이라 실행하지 않았다.
- 같은 controller Queue family의 앞선 기록에는 focused Playwright가 local socket 권한으로 보류된 `local_socket_guard_auto_held` 상태가 남아 있다. 이번 검증은 controller-smoke pass, full-smoke pass, release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 verify에서는 되돌리지 않았다.
- 다음 같은 계열의 안전한 local slice는 server socket을 열지 않고 `ControllerHandler`가 `/controller-assets/js/queue-presentation.js`와 `/controller-assets/js/cozy.js` 요청을 asset response 경로로 전달하는지 고정하는 handler-level unit guard다.
