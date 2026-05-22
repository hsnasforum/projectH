# 2026-05-21 Claude print JSONL lane integration

## 변경 파일
- `pipeline_runtime/supervisor.py`
- `watcher_dispatch.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- `work/5/21/2026-05-21-claude-print-jsonl-lane-integration.md`

## 사용 skill
- `security-gate`: Claude lane의 셸 실행 경로와 watcher prompt 파일 기록 경계가 local-first, run-local `.pipeline/runs/<run_id>/task-hints/` 안에 머무는지 확인하기 위해 사용했습니다.
- `finalize-lite`: 구현 후 실행한 검증, 미실행 범위, 문서 동기화 필요 여부, `/work` closeout 필요 여부를 정리하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- Claude lane을 기존 PTY interactive `lane-wrapper` 경로에서 `claude-print-jsonl-pipe` 기반 stdin-pipe JSONL 경로로 전환하는 후속 slice입니다.
- watcher가 Claude pane에 `tmux send-keys`로 직접 prompt를 붙여 넣는 대신, 같은 run의 task-hints 디렉터리에 pending prompt 파일을 원자적으로 기록해야 했습니다.
- Codex/Gemini lane의 기존 send-keys 경로는 그대로 유지해야 했습니다.

## 핵심 변경
- `RuntimeSupervisor._lane_shell_command()`가 lane 이름 `Claude` 또는 `lanes.json`의 `pane_type: "claude"`인 lane에 대해 새 `_claude_print_lane_shell_command()`를 반환하도록 분기했습니다.
- Claude watchdog shell command는 tmux pane 안에서 `claude.prompt.pending`을 감시하고, pending prompt를 `.claude.prompt.active`로 옮긴 뒤 현재 Python 실행 파일로 `-m pipeline_runtime.cli claude-print-jsonl-pipe`를 실행합니다. 실행 중 새 pending 파일을 삭제하지 않도록 active 파일을 별도로 사용합니다.
- 기존 non-Claude lane은 `pipeline_runtime.cli lane-wrapper` 경로와 `_lane_vendor_command()` 기반 셸 명령을 유지합니다.
- `WatcherDispatchQueue.dispatch()`는 Claude intent에서 pane readiness와 `send-keys`를 건너뛰고 `.pipeline/runs/<run_id>/task-hints/claude.prompt.pending`에 temp-write 후 rename 방식으로 prompt를 기록합니다.
- `PIPELINE_RUNTIME_RUN_ID`와 control 파일의 `.pipeline` 위치를 사용해 production watcher에서도 별도 `watcher_core.py` 변경 없이 task-hints 경로를 계산합니다.
- supervisor와 watcher dispatch 테스트에 Claude print watchdog 선택, pane_type fallback, Claude pending 파일 기록, non-Claude send-keys 유지 검증을 추가했습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/supervisor.py watcher_dispatch.py`
  - 결과: PASS, 출력 없음.
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_lane_shell_command_uses_claude_print_watchdog_for_claude tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_lane_shell_command_uses_pane_type_to_select_claude_print_watchdog -v`
  - 결과: `Ran 2 tests`, `OK`.
- 통과: `python3 -m unittest tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_claude_dispatch_writes_pending_prompt_file_without_send_keys tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_non_claude_dispatch_keeps_send_keys_path -v`
  - 결과: `Ran 2 tests`, `OK`.
- 통과: `python3 -c "... RuntimeSupervisor ... _lane_shell_command('Claude') ... _lane_shell_command('Codex') ..."`
  - 결과: `OK`.
- 통과: `git diff --check -- pipeline_runtime/supervisor.py watcher_dispatch.py`
  - 결과: PASS, 출력 없음.
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor -v 2>&1 | tail -5`
  - 결과: `Ran 221 tests in 2.303s`, `OK`.
- 통과: `python3 -m unittest tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest -v`
  - 결과: `Ran 16 tests in 0.052s`, `OK`.

## 남은 리스크
- live `claude` 실행, 실제 tmux watchdog pane 동작, JSONL wrapper event end-to-end 운영 확인은 이번 slice의 OUT_OF_SCOPE라 실행하지 않았습니다.
- prompt pending 파일은 atomic replace 방식이라 watchdog이 집기 전 여러 Claude dispatch가 연속으로 오면 마지막 pending prompt가 남습니다. 기존 dispatch dedupe/turn gate가 중복 dispatch를 줄이는 전제는 유지됩니다.
- 제품 문서 변경은 하지 않았습니다. 이번 변경은 document-first MVP의 사용자 기능이 아니라 내부 Claude lane transport 전환입니다.
- commit, push, branch/PR publication, PR creation, merge, release, publication은 실행하지 않았습니다.
