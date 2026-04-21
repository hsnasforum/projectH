# 2026-04-21 watcher self-restart stale busy tail

## 변경 파일
- `pipeline_runtime/lane_surface.py`
- `pipeline_runtime/supervisor.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/21/2026-04-21-watcher-self-restart-stale-busy-tail.md`

## 사용 skill
- `security-gate`: runtime watcher 재시작 경계가 operator decision, lane session 재시작, commit/push/PR boundary로 번지지 않는지 확인했습니다.
- `doc-sync`: `.pipeline/README.md`와 runtime 기술/운영 문서를 현재 동작에 맞췄습니다.
- `work-log-closeout`: 변경 파일, 검증, 남은 리스크를 표준 `/work` 형식으로 남깁니다.

## 변경 이유
- 6h synthetic soak 중 verify follow-up prompt가 Codex/Claude pane의 stale busy tail 때문에 계속 deferred 되는 상태가 관측됐습니다.
- 이전 구현은 watcher 코드가 바뀐 뒤에도 live old watcher process가 계속 떠 있으면 operator가 수동으로 재시작을 선택해야 했습니다.
- 이번 라운드는 이 두 경계를 runtime 내부에서 처리해, 실제 위험이 없는 watcher reload를 operator decision으로 올리지 않게 합니다.

## 핵심 변경
- `pipeline_runtime/lane_surface.py`는 최근 tail 안에서 단순 `Working (...)` 뒤에 `❯` / `›` / `>` 입력 prompt가 다시 보이면 prompt-ready를 우선합니다.
- 다만 `background terminal`, `thinking with ...`, `esc to interrupt/cancel` 같은 active busy marker가 같은 tail에 있으면 기존처럼 busy로 유지합니다.
- `pipeline_runtime/supervisor.py`는 experimental watcher source와 watcher가 직접 import하는 runtime helper가 live `.pipeline/experimental.pid`보다 새로우면 watcher만 self-restart하고 `watcher_self_restart_started` / `watcher_self_restart_completed` / `watcher_self_restart_failed` event를 남깁니다.
- watcher shell command 생성을 `_watcher_shell_command()` / `_spawn_experimental_watcher()`로 분리해 initial spawn과 self-restart가 같은 command path를 재사용합니다.
- 회귀 테스트는 stale busy prompt-ready, active busy 유지, watcher source self-restart event/de-dupe를 확인합니다.
- 문서는 stale busy tail 해석과 watcher self-restart가 operator boundary가 아니라 runtime-local reload임을 명시했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/lane_surface.py pipeline_runtime/supervisor.py`
  - 출력 없음, `rc=0`
- `python3 -m py_compile pipeline_runtime/lane_surface.py pipeline_runtime/supervisor.py watcher_core.py`
  - 출력 없음, `rc=0`
- `python3 -m unittest tests.test_watcher_core.PanePromptDetectionTest.test_claude_code_prompt_after_busy_tail_counts_as_ready`
  - `Ran 1 test`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_watcher_source_change_restarts_watcher_without_operator_decision`
  - `Ran 1 test`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_busy_tail_wins_over_prompt_footer_for_active_claude_lane tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_verify_lane_background_terminal_wait_surfaces_working`
  - `Ran 2 tests`, `OK`
- `python3 -m unittest tests.test_watcher_core.PanePromptDetectionTest.test_claude_code_prompt_after_busy_tail_counts_as_ready tests.test_watcher_core.PanePromptDetectionTest.test_old_busy_scrollback_does_not_block_current_ready_prompt`
  - `Ran 2 tests`, `OK`
- `python3 -m unittest tests.test_watcher_core`
  - `Ran 161 tests`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - `Ran 120 tests`, `OK`
- `git diff --check -- pipeline_runtime/lane_surface.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 출력 없음, `rc=0`

## 남은 리스크
- 이미 실행 중이던 synthetic soak supervisor/watcher process는 이 Python 변경을 메모리에 다시 import하지 않습니다. 이번 self-restart 경계는 다음 supervisor poll이 새 코드를 실행하는 run부터 적용됩니다.
- self-restart는 experimental watcher process만 교체합니다. tmux watcher window 정리까지 포함한 window reuse/cleanup은 이번 범위 밖입니다.
- 6시간 soak 자체는 이번 라운드에서 새로 완주하지 않았고, focused replay와 supervisor/watcher unit suite로 검증했습니다.
