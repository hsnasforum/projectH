# 2026-05-18 runtime dispatch stall clear retry

## 변경 파일

- `verify_fsm.py`
- `watcher_core.py`
- `tests/test_watcher_core.py`
- `work/5/18/2026-05-18-runtime-dispatch-stall-clear-retry.md`

## 사용 skill

- `security-gate`: Codex tmux 입력 정리와 watcher 런타임 재시작이 local runtime control 및 shell/tmux 경계에 닿는지 점검했습니다.
- `work-log-closeout`: 이번 런타임 복구 라운드의 변경 파일, 실행 검사, 남은 리스크를 표준 `/work` 형식으로 기록했습니다.

## 변경 이유

- 런처 화면과 `status --json`에서 `dispatch_stall`, `dispatch_backoff_same_snapshot`, `prompt_visible` 계열로 verify dispatch가 고착된 상태를 확인했습니다.
- 원인은 이전 dispatch의 Codex verify 프롬프트가 입력창에 남아 있는데, `verify_fsm.py`가 이 상태를 계속 같은 스냅샷으로만 suppress하고 지우거나 재전송하지 않는 흐름이었습니다.
- 현실적인 복구 범위는 publication, stash, branch/PR, merge를 건드리지 않고 로컬 watcher가 stale prompt를 정리한 뒤 같은 verify를 재전송하게 하는 것입니다.

## 핵심 변경

- `StateMachine`에 `clear_failed_dispatch_input` 콜백을 추가했습니다.
- `verify_fsm.py`가 failed dispatch backoff 이후 현재 verify 프롬프트 marker를 Codex pane에서 다시 발견하면, stale input을 지우고 dedupe를 해제한 뒤 재전송 경로로 진행하게 했습니다.
- `watcher_core.py`에서 기존 `watcher_dispatch.clear_codex_failed_dispatch_input()`을 FSM에 연결했습니다.
- `tests/test_watcher_core.py`의 visible prompt backoff 테스트를 새 동작에 맞춰 stale prompt cleanup 후 redispatch를 검증하도록 갱신했습니다.
- 런타임은 `python3 -m pipeline_runtime.cli restart --no-attach /home/xpdlqj/code/projectH`로 재시작해 새 watcher 코드를 로드했습니다.
- 재시작 후 `status --json`에서 automation `ok`, `VERIFY_RUNNING`, `dispatch_seen seq 1916`까지 회복된 것을 확인했습니다.

## 검증

- `python3 -m py_compile verify_fsm.py watcher_core.py watcher_dispatch.py watcher_prompt_assembly.py tests/test_watcher_core.py tests/test_verify_fsm.py`
  - 통과.
- `python3 -m unittest -v tests.test_watcher_core.VerifyPendingBackoffTest`
  - 통과. `Ran 7 tests`, `OK`.
- `python3 -m unittest -v tests.test_verify_fsm tests.test_watcher_core.VerifyPendingBackoffTest`
  - 통과. `Ran 17 tests`, `OK`.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_control_writers tests.test_pipeline_runtime_schema tests.test_pipeline_runtime_supervisor tests.test_verify_fsm tests.test_watcher_core`
  - 통과. `Ran 526 tests in 12.362s`, `OK`.
- `python3 -m pipeline_runtime.cli doctor --json`
  - 통과. `fail=0`, `warn=0`, `ok=13`.
- `python3 -m pipeline_runtime.cli status --json`
  - 재시작 전 `automation_health=recovering`, `automation_reason_code=dispatch_stall`, `active_round.status=VERIFY_PENDING`, `dispatch_stage=dispatch_send_failed`를 확인했습니다.
  - 재시작 후 `runtime_state=RUNNING`, `automation_health=ok`, `active_round.status=VERIFY_RUNNING`, `dispatch_control_seq=1916`, Codex lane `dispatch_seen seq 1916`을 확인했습니다.

## 남은 리스크

- 이번 변경은 local runtime dispatch 복구에 한정했습니다. Playwright, `make e2e-test`, local socket/server startup, long soak는 실행하지 않았습니다.
- `stash@{0}`는 적용/삭제/검증하지 않았고 그대로 보존했습니다.
- commit, push, branch/PR publication, PR creation/reuse, merge, release, external publication, readiness claim은 수행하지 않았습니다.
- live 1916 verify는 `TASK_DONE` 이후 `/verify` receipt가 없어 `receipt_close_pending`으로 남아 있었으므로, 같은 라운드에서 별도 `/verify` 기록으로 닫아야 합니다.
