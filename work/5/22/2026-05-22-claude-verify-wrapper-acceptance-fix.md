# 2026-05-22 Claude verify wrapper acceptance fix

## 변경 파일
- `pipeline_runtime/cli.py`
- `verify_fsm.py`
- `watcher_core.py`
- `tests/test_pipeline_runtime_cli.py`
- `tests/test_verify_fsm.py`
- `work/5/22/2026-05-22-live-claude-verify-trigger.md`
- `work/5/22/2026-05-22-live-claude-verify-trigger-2.md`
- `work/5/22/2026-05-22-live-claude-verify-trigger-3.md`
- `work/5/22/2026-05-22-claude-verify-wrapper-acceptance-fix.md`

## 사용 skill
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, live 이벤트 근거, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- live Claude verify lane 검증 중 watchdog은 기동됐지만 verify dispatch가 `claude.prompt.pending` 파일을 만들지 않아 기존 tmux send-keys 경로로 빠지는 문제가 확인됐습니다.
- 이후 `claude-print-jsonl-pipe`가 Claude `--print` stdout을 프로세스 종료 후에야 처리해 `TASK_ACCEPTED`가 accept deadline 전에 기록되지 않는 문제가 추가로 확인됐습니다.
- 목표 조건은 자연스러운 implement -> verify 사이클에서 `events.jsonl`에 `TASK_ACCEPTED source=wrapper lane=Claude`가 기록되는지 확인하는 것이었습니다.

## 핵심 변경
- `verify_fsm.StateMachine`에 Claude verify lane용 task hint writer 주입점을 추가해, Claude verify dispatch 전에 `dispatch_id`와 task hint를 먼저 기록할 수 있게 했습니다.
- `watcher_core.py`에서 Claude verify lane은 tmux send-keys 대신 `run_dir/task-hints/claude.prompt.pending`을 atomic write하도록 분기했습니다.
- `watcher_core.py`에서 `claude.json` active task hint를 `job_id`, `dispatch_id`, `control_seq`와 함께 기록해 wrapper가 동일 dispatch를 식별할 수 있게 했습니다.
- `pipeline_runtime/cli.py`에서 `claude-print-jsonl-pipe`가 stdout을 line-by-line으로 실시간 처리하도록 바꿨습니다.
- Claude stream-json의 `assistant` 이벤트도 wrapper activity로 인정해 `TASK_ACCEPTED`가 프로세스 종료 전에 발생하도록 했습니다.
- 세 차례 live trigger note로 implement -> verify 사이클을 재생했고, 세 번째 run에서 wrapper 기반 Claude 수락 이벤트를 확인했습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/cli.py verify_fsm.py watcher_core.py tests/test_pipeline_runtime_cli.py tests/test_verify_fsm.py`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli tests.test_verify_fsm -v 2>&1 | tail -12`
  - 결과: `Ran 67 tests in 0.225s`, `OK`
- 통과: `python3 -m unittest tests.test_watcher_core -v 2>&1 | tail -5`
  - 결과: `Ran 264 tests in 9.392s`, `OK`
- 통과: `git diff --check -- pipeline_runtime/cli.py verify_fsm.py watcher_core.py tests/test_pipeline_runtime_cli.py tests/test_verify_fsm.py`
- live 확인:
  - run: `.pipeline/runs/20260522T040034Z-p31147/events.jsonl`
  - 확인 이벤트: `TASK_ACCEPTED source=wrapper lane=Claude`
  - job_id: `20260522-2026-05-22-live-claude-verify-tr-5425a718`
  - dispatch_id: `f0603b6bd6b9887ba6c13dc4ba5c88ab20f8b881`
- 정리 확인:
  - `python3 -m pipeline_runtime.cli status . --json`에서 `runtime_state=STOPPED`
  - `.pipeline/config/agent_profile.json`은 `selected_agents=['Codex']`, `role_bindings.verify='Codex'`로 원복 확인

## 남은 리스크
- 이번 확인은 `TASK_ACCEPTED source=wrapper lane=Claude` 조건까지입니다. `TASK_DONE`까지의 end-to-end 완료는 Claude 응답 완료 시간과 후속 verify note 생성까지 포함하는 별도 운영 확인이 필요합니다.
- 같은 run 안에 dispatch 전 supervisor `pane_text_fallback_used lane=Claude` 이벤트가 몇 차례 남아 있습니다. wrapper 수락 자체는 확인됐지만, fallback 노이즈를 줄이는 작업은 별도 슬라이스로 분리하는 것이 안전합니다.
- `.pipeline/config/agent_profile.json.before-live-claude-confirm-3` 백업 파일은 삭제하지 않고 남겼습니다. 불필요하면 후속 정리 커밋에서 제거할 수 있습니다.
- commit, push, PR 생성, merge는 실행하지 않았습니다.
