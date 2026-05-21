# 2026-05-20 controller Queue asset fail-closed guard

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-queue-asset-fail-closed-guard.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2048`가 server socket 없이 missing/traversal-style controller asset 요청이 JSON `HTTPStatus.NOT_FOUND`로 fail-closed 되는지 unit guard로 고정하라고 지시했다.
- 직전 handler asset response guard는 실제 Queue JS asset의 성공 응답 경로를 확인했지만, bad asset 요청이 raw file bytes나 cacheable JS asset response로 새지 않는지는 직접 확인하지 않았다.

## 핵심 변경
- `tests/test_controller_server.py`의 `ControllerAssetResolutionTests`에 `test_serve_controller_asset_fails_closed_for_bad_paths`를 추가했다.
- `_serve_controller_asset("js/missing-queue-helper.js")`가 `HTTPStatus.NOT_FOUND`와 JSON 응답을 반환하는지 확인했다.
- `_serve_controller_asset("../server.py")`도 동일하게 JSON `HTTPStatus.NOT_FOUND`로 닫히는지 확인했다.
- fail-closed 응답이 `Cache-Control` asset header를 반환하지 않고, `Content-Type`에 `javascript`를 포함하지 않으며, body가 `{"error": "asset not found"}`인지 확인했다.
- `controller/server.py` 생산 코드는 수정하지 않았다.

## 검증
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 33 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free handler fail-closed unit guard만 추가했다. Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- 같은 controller Queue family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 상태가 남아 있다. 이번 라운드는 controller-smoke pass나 release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 라운드에서는 `tests/test_controller_server.py`와 이 `/work` 기록 외에는 의도적으로 건드리지 않았다.
