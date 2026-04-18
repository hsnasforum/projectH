# 2026-04-18 supervisor inherits live watcher run_id

## 변경 파일
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `.pipeline/README.md`

## 사용 skill
- `doc-sync`: supervisor restart 시 watcher run_id 인계 계약을 `.pipeline/README.md`에 현재 구현 truth로 맞추기 위해 사용했습니다.
- `work-log-closeout`: 이번 라운드 closeout을 repo 규칙 형식으로 남기기 위해 사용했습니다.

## 변경 이유
- 직전 라운드의 `verify/4/18/2026-04-18-watcher-startup-pending-verify-replay-verification.md`는 watcher 쪽 startup `VERIFY_PENDING` replay와 stale `slot_verify` lease 정리를 unit으로 다시 닫았지만, 같은 family의 남은 current-risk로 "live restart 뒤 canonical `.pipeline/runs/<run_id>/status.json`이 stale `STOPPED` snapshot에 머무는 문제"를 명시적으로 남겼습니다.
- 핸드오프(`STATUS: implement`, `CONTROL_SEQ: 308`)가 지목한 root cause는 status rendering이 아니라 supervisor/watcher current-run 동기화였습니다. supervisor는 재시작될 때마다 매번 새 `run_id`를 만들고 새 `runs/<run_id>/` 디렉터리에 쓰기 때문에, watcher가 이미 살아 있는 동안에는 supervisor가 보는 `load_job_states(... run_id=self.run_id ...)`가 비어 buffer가 비고, 이전 supervisor가 남긴 옛 `runs/<old>/status.json`은 그대로 stale `STOPPED`로 남았습니다.
- 그래서 watcher가 startup-replay한 current-run `VERIFY_PENDING` job state가 분명히 존재해도 canonical runtime surface는 verify truth를 즉시 따라오지 않았습니다.

## 핵심 변경
- `pipeline_runtime/supervisor.py`
  - `RuntimeSupervisor.__init__`이 `run_id`를 명시적으로 받지 않은 경우, 새 helper `_inherited_run_id_from_live_watcher()`를 먼저 호출해 `.pipeline/experimental.pid`가 가리키는 watcher pid가 살아 있을 때만 `.pipeline/current_run.json`의 기존 `run_id`를 그대로 이어받도록 했습니다.
  - 이렇게 하면 watcher가 이미 들고 있는 current-run job state(`VERIFY_PENDING` / `VERIFY_RUNNING`)와 supervisor의 `load_job_states(... run_id=self.run_id ...)` 필터가 같은 `run_id`로 정렬되므로, supervisor가 같은 `runs/<run_id>/status.json`을 새로 덮어쓰면서 `active_round.state`가 `VERIFY_PENDING` / `VERIFYING`으로 즉시 surface됩니다.
  - watcher pid가 죽었거나 `experimental.pid` 자체가 없을 때는 helper가 빈 문자열을 돌려주므로, 기존 fresh-start 경로(`_make_run_id()`)는 그대로 유지됩니다. supervisor가 이미 explicit `--run-id`를 전달받는 daemon entry나 launcher의 fresh spawn 경로도 동작이 변하지 않습니다.
- `tests/test_pipeline_runtime_supervisor.py`
  - `test_supervisor_inherits_run_id_when_watcher_is_alive_so_status_follows_verify_replay`를 추가했습니다.
    - prior `runs/<old>/status.json`에 `runtime_state: STOPPED`, `active_round: null` snapshot을 깔아두고, `current_run.json`이 그 `run_id`를 가리키며, `experimental.pid`가 현재 python pid를 가리켜 watcher가 살아 있는 상황을 만든 뒤, 새 supervisor를 explicit `run_id` 없이 만들어 `_write_status()`까지 한 번 돌립니다.
    - supervisor가 `old_run_id`를 그대로 인계받고, 같은 `runs/<old_run_id>/status.json`을 덮어써 `runtime_state != "STOPPED"`이고 `active_round.state == "VERIFY_PENDING"`이 되는지 고정합니다.
  - `test_supervisor_skips_run_id_inheritance_when_watcher_pid_is_dead`를 추가해, `experimental.pid`가 죽은 pid를 가리킬 때는 helper가 fall-through로 fresh `_make_run_id()`를 그대로 쓰는지 negative path도 같이 잡았습니다.
- `.pipeline/README.md`
  - 기존 "watcher가 supervisor의 current `run_id`를 그대로 써야 한다" 항목 바로 다음에, "반대로 supervisor가 재시작될 때 watcher가 살아 있다면 supervisor가 `current_run.json`의 기존 `run_id`를 이어받는다"는 한 문장을 추가해, canonical runtime surface 동기화 경계를 양방향으로 명시했습니다.

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
- live tmux restart 뒤 실제 `runs/<run_id>/status.json`이 verify replay를 실시간으로 따라오는지 재현은 이번 라운드에서 다시 돌리지 않았습니다. 이유는 새 ownership 경계를 unit 두 개와 기존 supervisor 상태 회귀 75개로 직접 고정했고, broad live soak는 launcher/wrapper-event/state-writer 계약이 같이 바뀌지 않은 이번 변경 범위에 비해 과한 증명이기 때문입니다.

## 남은 리스크
- 이번 변경은 supervisor가 `experimental.pid`가 가리키는 pid를 통해 "watcher 살아 있음"을 판정합니다. 같은 pid가 다른 프로세스로 재사용되는 극단적인 경우(예: long uptime + pid wrap)에는 잘못된 인계가 일어날 수 있습니다. 다만 같은 pid file은 supervisor가 spawn할 때마다 재기록되고, watcher는 supervisor가 바로 다시 spawn하므로 현재 라운드의 stop/restart 윈도우에서는 실질 위험이 작다고 판단했습니다.
- 매우 오래된 `current_run.json`이 archive되지 않은 상태에서 같은 pid file이 우연히 살아 있는 별도 watcher와 매칭되면, supervisor가 이미 의미가 없는 prior `run_id`로 status를 다시 쓸 수 있습니다. 다음 same-family follow-up은 이 경계를 더 좁히는 owner-fingerprint 비교(예: pid + start_time, 또는 watcher가 직접 `current_run.json`에 owner pid를 함께 기록)로 다룰 수 있습니다.
- launcher/controller 쪽 thin client는 여전히 `current_run.json` → `runs/<run_id>/status.json`을 따라 읽으므로, 이 라운드의 ownership 경계 변경 자체로 client가 보는 truth는 자동으로 더 정확해집니다. 다만 client side display contract(예: `STOPPED`였던 round를 어떻게 시각화했는지)는 이번 변경 범위 밖이라 별도 라운드에서 다뤄도 됩니다.
