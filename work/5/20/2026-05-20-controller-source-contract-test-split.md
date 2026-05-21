# 2026-05-20 controller source contract test split

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-source-contract-test-split.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2055`가 과도하게 커진 controller source-contract test를 목적별 테스트로 분리하라고 지시했다.
- 기존 `test_controller_html_polls_runtime_api_only`는 shell script ownership, runtime endpoint/source markers, action request shape, module-side panel truth, visual/source markers를 한 테스트에 섞고 있어 실패 원인과 shipped/module-side 경계가 흐려질 수 있었다.

## 핵심 변경
- `ControllerServerLaunchGateTests`에 `_controller_sources()` helper를 추가해 controller HTML/CSS/server/client source 읽기를 한 곳으로 모았다.
- 기존 큰 source-contract test를 `test_controller_shell_scripts_keep_shared_source_ownership`, `test_controller_shell_runtime_api_source_contract`, `test_controller_shell_action_request_shape_contract`, `test_controller_panel_request_shape_stays_module_side`, `test_controller_visual_source_markers_stay_available`로 분리했다.
- `index.html` 직접 script load/order, `cozy.js` runtime API/source markers, `cozy.js` POST/JSON action request shape, `zones.js` -> `panel.js` module-side import/request shape, visual/CSS/queue/source markers가 각각 독립적으로 실패하도록 정리했다.
- 기존 source assertion은 삭제하지 않고 목적별 테스트로 이동했다. 생산 코드(`controller/index.html`, `controller/js/*.js`, `controller/server.py`)는 수정하지 않았다.

## 검증
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 48 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free test organization/source-contract split만 수행했다. Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 상태가 남아 있다. 이번 라운드는 controller-smoke pass나 release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 라운드에서는 `tests/test_controller_server.py`와 이 `/work` 기록 외에는 의도적으로 건드리지 않았다.
