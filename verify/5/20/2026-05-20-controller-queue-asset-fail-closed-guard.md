# 2026-05-20 controller Queue asset fail-closed guard 검증

## 검증 대상
- `work/5/20/2026-05-20-controller-queue-asset-fail-closed-guard.md`
- `tests/test_controller_server.py`의 `ControllerAssetResolutionTests.test_serve_controller_asset_fails_closed_for_bad_paths`
- `controller/server.py`의 `_serve_controller_asset()` missing/traversal fail-closed 경로

## 변경 파일
- 이 검증 기록 파일 자체 외에는 없음.

## 실행한 확인
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 33 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/ verify/5/20/`
  - 통과.

## 판단
- 최신 `/work`의 변경 주장은 현재 코드와 일치한다.
- `test_serve_controller_asset_fails_closed_for_bad_paths`는 `_serve_controller_asset("js/missing-queue-helper.js")`와 `_serve_controller_asset("../server.py")`가 모두 `HTTPStatus.NOT_FOUND`로 응답하는지 확인한다.
- 해당 guard는 bad asset 응답이 JSON `Content-Type`, 정확한 `Content-Length`, `Access-Control-Allow-Origin: *`, `{"error": "asset not found"}` body를 반환하고 `Cache-Control` asset header나 JavaScript content type을 반환하지 않는지 확인한다.
- `controller/server.py` 생산 코드는 이번 구현 라운드에서 수정되지 않았다.
- 이번 verify 지시의 `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state=RUNNING`, `automation_health=recovering`, `automation_next_action=retrying`, active control `.pipeline/implement_handoff.md#2048`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`로 주어졌다. 따라서 lane-local `status --json`, `doctor --json`, `tmux` 명령은 런타임 생존성 판단에 사용하지 않았다.

## 남은 확인
- Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 이번 work 범위 밖이라 실행하지 않았다.
- 같은 controller Queue family의 앞선 기록에는 focused Playwright가 local socket 권한으로 보류된 `local_socket_guard_auto_held` 상태가 남아 있다. 이번 검증은 controller-smoke pass, full-smoke pass, release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 verify에서는 되돌리지 않았다.
- 다음 안전한 local slice는 server socket을 열지 않고 `ControllerHandler`의 `/`, `/controller`, `/controller/` shell route가 `_serve_html()`로 dispatch되고 실제 controller HTML 응답이 Queue script tags를 포함하는지 고정하는 handler-level unit guard다.
