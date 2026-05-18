# 2026-05-18 pipeline dispatch runtime recovery

## 변경 파일
- `watcher_prompt_assembly.py`
- `watcher_core.py`
- `watcher_dispatch.py`
- `verify_fsm.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_verify_fsm.py`
- `verify/5/18/2026-05-18-pipeline-stale-handoff-clean-recovery.md`
- `work/5/18/2026-05-18-pipeline-stale-handoff-clean-recovery.md`
- `work/5/18/2026-05-18-pipeline-stale-handoff-stash-inventory-guard.md`
- `work/5/18/2026-05-18-dirty-tracked-source-test-syntax-unit-guard.md`
- `work/5/18/2026-05-18-pipeline-dispatch-runtime-recovery.md`

## 사용 skill
- `security-gate`: tmux dispatch, runtime close-chain, log/status surface를 바꾸는 로컬 실행 경계라 승인/쓰기/감사 범위를 점검했습니다.
- `finalize-lite`: 의미 있는 runtime 복구 변경의 검증 사실, 문서 동기화 필요 여부, `/work` closeout 준비 상태를 정리했습니다.
- `work-log-closeout`: 이번 구현 라운드의 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- 워크트리 정리 과정에서 기존 dirty tree를 `stash@{0}`로 보존한 뒤, active handoff가 보존 전제와 어긋난 stale 상태가 되었습니다.
- verify prompt에는 `runtime_status_at_dispatch` 컨텍스트가 빠져 `KeyError`가 발생했고, Codex paste submit 실패 뒤 prompt가 남아 dispatch가 멈출 수 있었습니다.
- wrapper `TASK_ACCEPTED`/`TASK_DONE` 신호가 늦거나 누락될 때, 실제 pane은 작업 중이거나 산출물을 완료했는데도 runtime이 accept/done 대기나 `signal_mismatch`로 다음 단계 전환을 놓치는 경로가 확인되었습니다.
- 목표는 stash를 적용/삭제하지 않고, launcher/watcher가 실제 완료 산출물과 lane 상태를 근거로 다음 로컬 control까지 진행하게 만드는 것입니다.

## 핵심 변경
- verify prompt context에 `RUNTIME_STATUS_AT_DISPATCH`, advisory disabled 상황의 next-control 옵션, lane-local runtime command guard를 포함했습니다.
- Codex dispatch가 paste 후 Enter/C-j에도 prompt를 소비하지 못하면 prompt를 정리하고 literal fallback dispatch를 시도하도록 했습니다.
- `DISPATCH_SEEN`/`TASK_ACCEPTED`가 supervisor `lane_working`보다 약간 먼저 찍히는 같은 `control_seq` 경계는 `signal_mismatch`로 버리지 않도록 했습니다.
- verify FSM은 Codex lane이 실제로 바쁘면 accept deadline을 연장하고, `/verify`와 다음 control이 완성된 뒤 Codex가 idle로 안정되면 누락된 `TASK_DONE`을 추론해 round를 닫도록 했습니다.
- live pipeline은 stale handoff recovery, stash inventory guard, dirty tracked source/test guard까지 진행했고, `stash@{0}`는 계속 보존했습니다.

## 검증
- `python3 -m py_compile watcher_dispatch.py watcher_prompt_assembly.py watcher_core.py verify_fsm.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py tests/test_verify_fsm.py`: PASS, 출력 없음.
- `python3 -m unittest -v tests.test_watcher_core.WatcherPromptAssemblyTest tests.test_watcher_core.CodexDispatchConfirmationTest`: PASS.
- `python3 -m unittest -v tests.test_verify_fsm.VerifyFsmSnapshotCloseTest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_verify_prompt_prefers_gemini_before_operator_for_slice_ambiguity`: PASS.
- `python3 -m unittest -v tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_dispatch_signal_mismatch_supervisor_working_without_wrapper_receipt tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_signal_mismatch_keeps_pending_when_dispatch_seen_races_before_lane_working tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_signal_mismatch_does_not_drop_verify_followup_pending`: PASS.
- `python3 -m unittest -v tests.test_watcher_core.WatcherPromptAssemblyTest tests.test_watcher_core.CodexDispatchConfirmationTest tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest tests.test_verify_fsm.VerifyFsmSnapshotCloseTest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_verify_prompt_prefers_gemini_before_operator_for_slice_ambiguity`: PASS, 54 tests OK.
- `python3 -m unittest -v tests.test_verify_fsm.VerifyFsmSnapshotCloseTest.test_verify_outputs_close_when_codex_idle_without_task_done_after_grace tests.test_verify_fsm.VerifyFsmSnapshotCloseTest.test_verify_close_outputs_do_not_close_before_task_accept_and_done tests.test_verify_fsm.VerifyFsmSnapshotCloseTest.test_verify_accept_wait_extends_while_codex_lane_is_busy tests.test_verify_fsm.VerifyFsmSnapshotCloseTest.test_verify_close_chain_replays_task_accepted_task_done_then_receipt_close`: PASS, 4 tests OK.
- `git diff --check -- watcher_dispatch.py watcher_prompt_assembly.py watcher_core.py verify_fsm.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py tests/test_verify_fsm.py`: PASS, 출력 없음.
- live 확인: watcher가 `watcher_dispatch.py`/`verify_fsm.py` 변경 뒤 self-restart 되었고, `CONTROL_SEQ: 1904` implement, `CONTROL_SEQ: 1905` implement, 그 뒤 verify dispatch가 실제로 진행되었습니다.
- live 확인: `python3 -m pipeline_runtime.cli status --json /home/xpdlqj/code/projectH` 기준 runtime은 `RUNNING`, watcher alive, `automation_health: ok`, Codex lane `WORKING`, active round `VERIFY_RUNNING`, note `dispatch_seen seq 1905`였습니다.
- live 확인: `stash@{0}`는 `codex-clean-worktree-2026-05-18` 메시지로 보존되어 있고, apply/pop/drop/clear/branch/store/rewrite/discard하지 않았습니다.

## 남은 리스크
- 전체 unittest, Playwright, `make e2e-test`, controller smoke, local socket/server startup, long soak는 실행하지 않았습니다.
- live pipeline은 이 기록 작성 시점에 `work/5/18/2026-05-18-dirty-tracked-source-test-syntax-unit-guard.md` verify를 수행 중이었습니다. 완료까지는 다음 watcher cycle에서 `/verify`와 다음 control을 확인해야 합니다.
- `stash@{0}`는 572개 파일, 46429 insertions(+), 1273 deletions(-) 규모의 대형 보존물이라 후속 split/apply/discard 판단이 필요합니다.
- publication은 계속 held 상태입니다. commit, push, branch/PR publication, PR creation/reuse, merge, release, external publication, readiness claim은 수행하지 않았습니다.
