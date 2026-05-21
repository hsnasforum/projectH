# 2026-05-20 controller server runtime_snapshot export guard 검증

## 검증 대상
- `tests/test_controller_server.py`의 socket-free controller server guard
- legacy runtime status payload의 `runtime_snapshot` 합성 확인
- unavailable/non-mapping runtime placeholder의 stopped snapshot 확인
- Queue presentation literal ownership assertion 갱신

## 변경 파일
- 검증 기록 파일 자체 외에는 없음.

## 실행한 확인
- `python3 -m py_compile controller/server.py tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 29 tests 통과.
- `git diff --check -- controller/server.py tests/test_controller_server.py work/5/20/ verify/5/20/`
  - 통과.

## 판단
- 최신 `/work`의 변경 주장은 현재 코드와 일치한다.
- `get_runtime_status()` legacy payload 경로는 reducer-owned `runtime_snapshot.contract_version == 2026-05-20.runtime_snapshot_v1`을 포함하며, active implement control을 Queue `implement #2043`으로 표면화하는 단위 테스트가 추가되어 있다.
- unavailable/non-mapping runtime placeholder 경로는 stopped `runtime_snapshot`과 Queue `Runtime inactive`를 포함하도록 단위 테스트가 보강되어 있다.
- Queue literal `No queued pipeline task`의 소유 파일이 `controller/js/cozy.js`에서 `controller/js/queue-presentation.js`로 이동한 사실을 반영해 기존 stale assertion이 갱신되어 있다.
- `controller/server.py` 생산 코드는 이번 라운드에서 수정되지 않았다.
- 이번 verify 지시의 `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state=RUNNING`, `automation_health=recovering`, `automation_next_action=retrying`, active control `.pipeline/implement_handoff.md#2043`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`로 주어졌다. 따라서 lane-local `status --json`, `doctor --json`, `tmux` 명령은 런타임 생존성 판단에 사용하지 않았다.

## 남은 확인
- Playwright, full controller smoke, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 이번 work 범위 밖이라 실행하지 않았다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 verify에서는 되돌리지 않았다.
- 다음 같은 계열의 안전한 local slice는 `/api/runtime/monitor-snapshot` 계열이 `get_runtime_status()`에서 받은 `runtime_snapshot`을 드롭하지 않는다는 socket-free server guard를 추가하는 것이다.
