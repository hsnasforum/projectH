# 2026-05-20 controller Queue asset resolution guard

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-queue-asset-resolution-guard.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2046`가 `_resolve_controller_asset()`이 실제 `controller/js/queue-presentation.js`와 `controller/js/cozy.js` 파일을 JS content type으로 해석하는지 socket-free unit guard로 고정하라고 지시했다.
- 직전 script-order guard는 HTML 로드 순서를 확인했지만, 실제 asset resolver가 Queue helper 파일을 제공할 수 있는지는 직접 확인하지 않았다.

## 핵심 변경
- `tests/test_controller_server.py`의 `ControllerAssetResolutionTests`에 `test_resolve_real_controller_queue_js_assets`를 추가했다.
- `_resolve_controller_asset("js/queue-presentation.js")`가 실제 `controller/js/queue-presentation.js` 경로를 반환하는지 확인했다.
- `_resolve_controller_asset("js/cozy.js")`가 실제 `controller/js/cozy.js` 경로를 반환하는지 확인했다.
- 두 asset의 content type에 `javascript`가 포함되는지 확인했다.
- `controller/server.py` 생산 코드는 수정하지 않았다.

## 검증
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 30 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free asset-resolution unit guard만 추가했다. Playwright, full controller smoke, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 라운드에서는 `tests/test_controller_server.py`와 이 `/work` 기록 외에는 의도적으로 건드리지 않았다.
