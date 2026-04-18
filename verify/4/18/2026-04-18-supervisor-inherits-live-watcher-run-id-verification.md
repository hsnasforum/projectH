# 2026-04-18 supervisor inherits live watcher run_id verification

## 변경 파일
- `verify/4/18/2026-04-18-supervisor-inherits-live-watcher-run-id-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-supervisor-inherits-live-watcher-run-id.md`가 supervisor restart 뒤 stale `STOPPED` runtime snapshot 문제를 `run_id` inheritance로 닫았다고 주장하므로, 현재 트리 기준으로 그 구현과 검증 결과가 실제로 맞는지 다시 확인해야 했습니다.
- same-day 기존 `/verify`인 `verify/4/18/2026-04-18-watcher-startup-pending-verify-replay-verification.md`는 직전 watcher replay 라운드를 닫은 note라서, latest `/work`를 직접 참조하는 새 canonical verify note가 필요했습니다.

## 핵심 변경
- latest `/work`의 핵심 구현 주장은 현재 코드와 일치했습니다.
  - `pipeline_runtime/supervisor.py`의 `RuntimeSupervisor.__init__`는 explicit `run_id`가 없을 때 `_inherited_run_id_from_live_watcher()`를 먼저 보고, `.pipeline/experimental.pid`가 가리키는 watcher pid가 살아 있으면 `.pipeline/current_run.json`의 기존 `run_id`를 이어받습니다.
  - 따라서 watcher가 이미 저장한 current-run job state를 supervisor의 `load_job_states(... run_id=self.run_id ...)` 필터가 같은 `run_id`로 다시 읽을 수 있고, stale old `status.json` 대신 같은 `runs/<run_id>/status.json`을 계속 갱신하는 경계가 현재 코드에 존재합니다.
  - `.pipeline/README.md`도 같은 양방향 ownership 계약을 현재 구현 truth로 적고 있습니다.
- latest `/work`가 적은 focused regression 2개는 현재 트리에서 그대로 통과했습니다.
  - live watcher pid + matching `current_run.json`이면 old run을 이어받아 `active_round.state == "VERIFY_PENDING"`로 surface하는 경로
  - watcher pid가 죽었으면 fresh `run_id`로 fall through 하는 negative path
- latest `/work`가 적은 broad regression도 current-tree truth로 다시 확인됐습니다.
  - `python3 -m unittest -v tests.test_pipeline_runtime_supervisor`는 현재 `Ran 75 tests`, `OK`
  - `python3 -m unittest -v tests.test_watcher_core`도 현재 `Ran 125 tests`, `OK`
- docs/plan 문맥도 이번 라운드와 충돌하지 않았습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 internal pipeline runtime이 여전히 supervisor-owned run-scoped surface라는 현재 phase truth를 유지하고 있어서, 이번 변경은 shipped browser contract를 넓히지 않고 같은 internal runtime family 안에 머뭅니다.
- 다만 latest `/work`가 남긴 residual risk, 즉 `experimental.pid`와 `current_run.json`을 live pid 하나로만 연결하는 경계는 이번 verify에서도 그대로 남았습니다.
  - stale pointer가 다른 live watcher와 섞일 가능성을 더 줄이려면, 다음 slice에서 `current_run` owner metadata를 같이 기록하고 supervisor inheritance에서 exact owner match를 요구하는 편이 맞습니다.

## 검증
- `python3 -m py_compile watcher_core.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_inherits_run_id_when_watcher_is_alive_so_status_follows_verify_replay tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_watcher_pid_is_dead`
  - 결과: `Ran 2 tests`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 75 tests`, `OK`
- `python3 -m unittest -v tests.test_watcher_core.VerifyCompletionContractTest.test_poll_replays_current_run_verify_pending_even_when_latest_work_is_already_verified`
  - 결과: `Ran 1 test`, `OK`
- `python3 -m unittest -v tests.test_watcher_core`
  - 결과: `Ran 125 tests`, `OK`
- `git diff --check -- watcher_core.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
  - 결과: 통과
- live tmux restart 뒤 실제 `runs/<run_id>/status.json` follow 여부는 이번 verify 라운드에서 다시 재현하지 않았습니다.
  - 이유: 이번 변경은 `run_id` ownership 경계와 supervisor status loading에 한정되고, unit 2개 + full supervisor/watcher regression이 이미 현재 트리에서 직접 통과했기 때문입니다.

## 남은 리스크
- `_inherited_run_id_from_live_watcher()`는 아직 `experimental.pid`의 live pid와 `current_run.json`의 `run_id`만으로 inheritance를 판단합니다. 그래서 stale `current_run.json`이 다른 live watcher와 섞이는 경우를 더 좁게 막지는 못합니다.
- 다음 same-family current-risk reduction은 `current_run.json`에 watcher owner metadata를 함께 기록하고, supervisor가 live `experimental.pid`와 exact owner match일 때만 run_id를 이어받게 하는 경계가 가장 작고 자연스럽습니다.
- extreme pid reuse 같은 더 드문 케이스는 그 다음 단계에서 `pid + start_time` 같은 stronger fingerprint로 다룰 수 있지만, 이번 라운드의 current-tree truth를 깨는 mismatch는 아니었습니다.
