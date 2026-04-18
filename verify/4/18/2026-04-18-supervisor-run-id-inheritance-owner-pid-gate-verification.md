# 2026-04-18 supervisor run_id inheritance owner pid gate verification

## 변경 파일
- `verify/4/18/2026-04-18-supervisor-run-id-inheritance-owner-pid-gate-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-supervisor-run-id-inheritance-owner-pid-gate.md`가 supervisor restart 뒤 `run_id` inheritance를 `current_run.json.watcher_pid == live experimental.pid`일 때만 허용하도록 좁혔다고 주장하므로, 현재 트리에서 그 구현과 검증 결과가 실제로 맞는지 다시 확인해야 했습니다.
- 같은 날 기존 `/verify`인 `verify/4/18/2026-04-18-supervisor-inherits-live-watcher-run-id-verification.md`는 직전 pid-less inheritance 라운드를 닫은 note라서, owner-pid gate까지 반영한 새 canonical verify note가 필요했습니다.

## 핵심 변경
- latest `/work`의 핵심 구현 주장은 현재 코드와 일치했습니다.
  - `pipeline_runtime/supervisor.py`의 `RuntimeSupervisor.__init__`는 explicit `run_id`가 없을 때 `_inherited_run_id_from_live_watcher()`를 먼저 보고, live watcher pid와 `current_run.json.watcher_pid`가 정확히 같을 때만 prior `run_id`를 이어받습니다.
  - `_write_current_run_pointer()`는 `current_run.json`에 `watcher_pid`를 함께 기록하고, `run()` 진입 직후와 각 `_write_status()` 끝에서 다시 써서 current pointer가 live watcher owner pid를 계속 따라가게 합니다.
  - `_coerce_pid()`와 `_live_experimental_watcher_pid()` 경계도 현재 코드에 있어 owner 필드 없음, mismatched pid, dead pid, 비정상 pid 값에서는 fresh `_make_run_id()`로 그대로 떨어집니다.
- latest `/work`가 적은 focused regression과 broad regression도 현재 트리에서 그대로 통과했습니다.
  - owner pid match positive path 1개, dead pid 1개, missing owner 1개, mismatched owner 1개, pointer write 1개가 모두 통과했습니다.
  - `tests.test_pipeline_runtime_supervisor` full suite도 현재 `Ran 78 tests`, `OK`로 유지됩니다.
  - watcher replay 경계 1개도 그대로 통과해 owner-pid gate가 current-run verify replay surface를 깨지 않음을 다시 확인했습니다.
- docs/plan 문맥도 이번 라운드와 충돌하지 않았습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 pipeline runtime을 여전히 internal/operator family로 두고 있어, 이번 변경은 browser shipped contract를 넓히지 않는 same-family current-risk reduction으로 남아 있습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_inherits_run_id_when_watcher_is_alive_so_status_follows_verify_replay tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_watcher_pid_is_dead tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_current_run_owner_pid_is_missing tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_current_run_owner_pid_mismatches_live_watcher tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_write_current_run_pointer_records_live_watcher_pid`
  - 결과: `Ran 5 tests`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 78 tests`, `OK`
- `python3 -m unittest -v tests.test_watcher_core.VerifyCompletionContractTest.test_poll_replays_current_run_verify_pending_even_when_latest_work_is_already_verified`
  - 결과: `Ran 1 test`, `OK`
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
  - 결과: 통과
- live tmux restart/replay는 이번 verify 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경은 supervisor의 inheritance gate와 `current_run.json` pointer payload에 한정되고, focused 5개 + full supervisor regression 78개 + watcher replay 1개가 현재 트리에서 직접 통과했기 때문입니다.

## 남은 리스크
- current inheritance gate는 여전히 pid 정수 비교만 봅니다. pid가 재사용되는 극단적인 경우에는 unrelated process가 같은 pid를 차지했을 때 stale pointer가 다시 살아날 여지가 남습니다.
- 다음 same-family current-risk reduction은 `watcher_pid`만이 아니라 live watcher process fingerprint(`pid + start_time` 등)를 `current_run.json`에 함께 기록하고, supervisor가 exact fingerprint match일 때만 prior `run_id`를 이어받게 하는 경계가 가장 작고 자연스럽습니다.
- cold start 직후 `watcher_pid: 0`이 잠깐 기록되는 창은 남아 있지만, 이 시점은 inheritance가 필요 없는 단계이고 이후 `_write_status()`에서 live pid로 다시 갱신되므로 현재 재현된 stale-mix risk와는 별개입니다.
