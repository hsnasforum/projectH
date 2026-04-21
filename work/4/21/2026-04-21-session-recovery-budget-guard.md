## 변경 파일
- `pipeline_runtime/supervisor.py`
- `pipeline_runtime/automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/04_QA_시험계획서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`

## 사용 skill
- `security-gate`
- `doc-sync`
- `work-log-closeout`

## 변경 이유
- 2026-04-21 09:18~09:23 UTC run log에서 `session_recovery_started` / `session_recovery_completed`가 5회 반복됐고, 각 회차마다 Claude/Codex/Gemini pane pid가 새 값으로 바뀌었습니다.
- `watcher_self_restart_*` event는 없었으므로 watcher source self-restart가 아니라 tmux session loss recovery가 scaffold를 반복 재생성한 문제였습니다.
- 원인은 supervisor가 `session_alive=True`를 한 번 관측하면 `_session_recovery_attempts`를 즉시 0으로 리셋해서, 짧게 살아난 session 뒤 다시 사라지는 패턴이 매번 "첫 복구"로 취급된 점입니다.

## 핵심 변경
- session loss scaffold recovery budget을 상수화하고, 자동 scaffold 재생성은 안정 윈도우 전 1회로 제한했습니다.
- 복구 뒤 같은 session이 300초 이상 안정적으로 살아 있을 때만 recovery budget을 리셋하도록 바꿨습니다.
- 안정 윈도우 전에 다시 session이 사라지면 두 번째 scaffold 재생성 대신 `session_recovery_exhausted` event를 남기고 `degraded_reasons`에 `session_missing`, `session_recovery_exhausted`를 함께 surface합니다.
- `automation_health`는 `session_recovery_exhausted`를 `needs_operator` / `operator_required`로 매핑해 반복 재시작 storm을 안전하게 멈추도록 했습니다.
- runtime README, 기술설계, QA, runbook에 `session_recovery_exhausted`와 300초 안정 윈도우 계약을 반영했습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/automation_health.py`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_automation_health`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_session_recovery_budget_resets_only_after_stable_alive_window tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_session_loss_does_not_recreate_scaffold_after_brief_alive_budget_hold tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_session_loss_failed_recovery_is_bounded_without_lane_restart_loop`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor`
- 통과: `git diff --check -- pipeline_runtime/supervisor.py pipeline_runtime/automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_automation_health.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/04_QA_시험계획서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- 확인: `.pipeline/current_run.json` 기준 현재 run은 `20260421T091515Z-p361782`, `runtime_state=STOPPED`, `watcher_pid=0`, supervisor/watcher pid file 없음.
- 실패/해당 없음: `python3 -m pipeline_runtime.cli status /home/xpdlqj/code/projectH --mode experimental`는 `status` subcommand가 없어 실행되지 않았습니다.

## 남은 리스크
- 이번 변경은 "session이 짧게 살아났다가 다시 사라질 때 scaffold를 반복 재생성하는 루프"를 막는 것입니다. tmux session 자체가 왜 외부에서 사라졌는지는 OS/tmux/process lifecycle 원인까지 별도로 보아야 합니다.
- 현재 runtime은 STOPPED 상태라 live session-loss smoke는 새 background automation을 띄우지 않기 위해 수행하지 않았습니다.
