# 2026-05-23 pty adapter pilot

## 변경 파일
- `watcher_pty_adapter.py`
- `tests/test_watcher_pty_adapter.py`
- `work/5/23/2026-05-23-pty-adapter-pilot.md`

## 사용 skill
- `onboard-lite`: CONTROL_SEQ 2158의 격리 파일럿 경계, 기존 `_lane_wrapper()` PTY reader 패턴, `TmuxAdapter` 공개 메서드 범위를 좁게 확인했습니다.
- `security-gate`: PTY/subprocess 기반 shell execution 파일럿이 local-first, 미연결, 승인 경계 불변인지 점검했습니다.
- `finalize-lite`: 실행한 검증과 미실행 범위, doc-sync 필요 여부, `/work` closeout 필요성을 정리했습니다.
- `work-log-closeout`: 실제 변경 파일, 검증 결과, 남은 리스크를 이 `/work` 노트로 기록했습니다.

## 변경 이유
- CONTROL_SEQ 2158 `a3_step9_pty_adapter_pilot` 지시에 따라 `tmux capture-pane` polling 모델의 대안이 될 PTY-native lane adapter를 격리 파일럿으로 추가해야 했습니다.
- 이번 단계는 future swap-in 준비만 수행하며, `watcher_core.py`, `TmuxAdapter`, supervisor, CLI runtime에는 연결하지 않습니다.
- PTY master fd reader thread와 직접 입력 전송 경로를 작은 모듈로 검증해, 이후 Step 10 여부를 판단할 수 있는 최소 기반을 마련합니다.

## 핵심 변경
- `watcher_pty_adapter.py`에 `PtyLane`을 추가했습니다. `pty.openpty()`, `subprocess.Popen(..., preexec_fn=os.setsid)`, background reader thread, `send()`, `capture()`, `kill()`, `health()`를 제공합니다.
- `watcher_pty_adapter.py`에 `PtyAdapter`를 추가했습니다. `spawn_lane`, `kill_lane`, `restart_lane`, `send_input`, `capture_tail`, `lane_health`, `session_exists`를 `TmuxAdapter` swap-in 후보 인터페이스에 맞췄습니다.
- reader thread는 master fd에서 4096-byte chunk를 읽고 UTF-8 replace decode 후 line buffer에 저장합니다. PTY close/EIO/EBADF는 thread exit로 처리합니다.
- 테스트는 real tmux나 long-running child에 의존하지 않도록 `socket.socketpair()`, `pty.openpty` mock, `subprocess.Popen` mock, `os.killpg` mock을 사용했습니다.
- 기존 런타임 연결 파일(`watcher_core.py`, `pipeline_runtime/tmux_adapter.py`, `pipeline_runtime/supervisor.py`, `pipeline_runtime/cli.py`)은 수정하지 않았습니다.

## 검증
- 통과: `python3 -m py_compile watcher_pty_adapter.py tests/test_watcher_pty_adapter.py`
- 통과: `python3 -m unittest tests.test_watcher_pty_adapter -v`
  - 결과: 7 tests OK
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_supervisor tests.test_watcher_core tests.test_watcher_status_writer tests.test_watcher_lane_status tests.test_watcher_recovery 2>&1 | tail -5`
  - 결과: 560 tests OK
- 통과: `git diff --check -- watcher_pty_adapter.py tests/test_watcher_pty_adapter.py`
- 통과: `git diff --check --no-index -- /dev/null watcher_pty_adapter.py; status1=$?; git diff --check --no-index -- /dev/null tests/test_watcher_pty_adapter.py; status2=$?; git diff --check --no-index -- /dev/null work/5/23/2026-05-23-pty-adapter-pilot.md; status3=$?; if [ "$status1" -gt 1 ] || [ "$status2" -gt 1 ] || [ "$status3" -gt 1 ]; then exit 1; fi`
  - 이유: 새 파일은 untracked 상태라 일반 `git diff --check`가 내용을 보지 못할 수 있어 보강 확인했습니다.

## 남은 리스크
- `PtyAdapter`는 아직 watcher/runtime에 연결되지 않은 격리 파일럿입니다. 현재 shipped behavior는 `TmuxAdapter` 기반 그대로입니다.
- 실제 장시간 PTY child, 터미널 크기, backpressure, attach/debug UX, wrapper event 통합은 이번 단계에서 검증하지 않았습니다.
- `PtyLane.kill()`은 `SIGTERM` 후 짧은 wait와 `SIGKILL` fallback을 갖지만, 실제 운영 연결 전에 process-group/FD lifecycle을 live smoke로 추가 확인해야 합니다.
- 문서 sync는 하지 않았습니다. 이번 변경은 미연결 내부 pilot module/test 추가이며 제품 동작, operator rule, approval contract를 변경하지 않습니다.
- commit, push, PR, merge, release는 실행하지 않았습니다. `PUBLISH_HELD: true` 유지입니다.
