# 2026-05-20 controller server runtime_snapshot export guard

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-server-runtime-snapshot-export-guard.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2043`가 controller server의 legacy runtime status와 placeholder 응답에 reducer-owned `runtime_snapshot`이 포함되는지 socket-free 단위 테스트로 고정하라고 지시했다.
- 기존 `tests.test_controller_server`는 Queue 문구가 `controller/js/queue-presentation.js`로 이동한 뒤에도 `controller/js/cozy.js`에서 해당 문구를 찾는 stale assertion 때문에 구현 전에도 실패했다.

## 핵심 변경
- `tests/test_controller_server.py`가 `RUNTIME_SNAPSHOT_CONTRACT_VERSION`을 직접 확인하도록 했다.
- `get_runtime_status()`가 legacy runtime payload에 `runtime_snapshot`을 합성하고, active implement control을 `queue.status == "implement #2043"`으로 표면화하는지 검증했다.
- unavailable/non-mapping runtime placeholder 경로가 stopped snapshot과 `Runtime inactive` Queue status를 포함하는지 기존 placeholder 테스트에 추가했다.
- Queue presentation literal ownership이 `cozy.js`가 아니라 `queue-presentation.js`에 있음을 반영해 stale assertion을 갱신했다.
- `controller/server.py`는 수정하지 않았다.

## 검증
- `python3 -m py_compile controller/server.py tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 29 tests 통과.
- `git diff --check -- controller/server.py tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free controller server unit guard만 추가했다. Playwright, full controller smoke, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 라운드에서는 `tests/test_controller_server.py`와 이 `/work` 기록 외에는 의도적으로 건드리지 않았다.
