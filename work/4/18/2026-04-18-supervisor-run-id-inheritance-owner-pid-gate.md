# 2026-04-18 supervisor run_id inheritance owner pid gate

## 변경 파일
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `.pipeline/README.md`

## 사용 skill
- `doc-sync`: supervisor `run_id` inheritance owner-match 게이트 계약을 `.pipeline/README.md`에 현재 구현 truth로 맞추기 위해 사용했습니다.
- `work-log-closeout`: 이번 라운드 closeout을 repo 규칙 형식으로 남기기 위해 사용했습니다.

## 변경 이유
- 직전 라운드 `work/4/18/2026-04-18-supervisor-inherits-live-watcher-run-id.md`와 `verify/4/18/2026-04-18-supervisor-inherits-live-watcher-run-id-verification.md`는 supervisor restart 뒤 stale `STOPPED` snapshot을 닫으려고 supervisor가 `current_run.json`의 `run_id`를 그대로 이어받게 했지만, inheritance 게이트는 아직 `experimental.pid`가 살아 있고 pointer에 `run_id`만 있으면 통과하는 수준이었습니다.
- 핸드오프(`STATUS: implement`, `CONTROL_SEQ: 309`)가 지목한 same-family current-risk는 명확합니다. 다른 watcher가 `experimental.pid`를 갱신했지만 `current_run.json`은 아직 이전 supervisor가 남긴 stale pointer라면, 새 supervisor가 잘못된 prior `run_id`를 그대로 이어받아 canonical runtime surface를 다시 어긋나게 만들 수 있었습니다.
- 그래서 이번 슬라이스에서는 inheritance를 supervisor가 `current_run.json`에 직접 기록한 `watcher_pid`와 현재 live `experimental.pid`가 정확히 같을 때만 허용하도록 한 단계 좁혔습니다.

## 핵심 변경
- `pipeline_runtime/supervisor.py`
  - 새 helper `_live_experimental_watcher_pid()`를 추가해 `experimental.pid` 파일이 가리키는 pid가 살아 있을 때만 그 정수를 돌리고, 없으면 `0`을 돌리는 단일 경계로 정리했습니다.
  - `_write_current_run_pointer()`가 매 호출에서 위 helper를 호출해 `current_run.json`에 `watcher_pid` 필드를 함께 기록합니다. supervisor 시작 시점 한 번(`run()` 진입)과, 이후 매 `_write_status()` 호출 끝부분(`_write_current_run_pointer()` 재호출)에서 `current_run.json`이 그때그때 살아 있는 watcher pid로 갱신됩니다. watcher가 spawn되기 전이거나 죽었으면 `watcher_pid: 0`이 적혀, inheritance가 실수로 살아나지 않습니다.
  - `_inherited_run_id_from_live_watcher()`는 이제 (a) `experimental.pid`가 가리키는 pid가 살아 있고, (b) `current_run.json`의 `run_id`가 비어 있지 않고, (c) 그 pointer의 `watcher_pid`가 위 live pid와 정확히 같을 때만 candidate `run_id`를 돌립니다. 그 외 모든 경우(파일 없음, 정수 변환 실패, 0 이하, owner 필드 없음, mismatched, 죽은 pid)는 빈 문자열을 돌려 fresh `_make_run_id()`가 그대로 이깁니다.
  - 작은 helper `_coerce_pid()`로 pointer payload가 int/float/str 어느 형태로 와도 안전하게 정수 pid로 변환하고, bool은 일부러 거절해 `True/False` 잡음이 owner 비교를 흐리지 않게 했습니다.
- `tests/test_pipeline_runtime_supervisor.py`
  - 기존 positive 회귀 `test_supervisor_inherits_run_id_when_watcher_is_alive_so_status_follows_verify_replay`의 `current_run.json` fixture에 `watcher_pid: os.getpid()`를 추가해 새 owner-match 계약 아래에서도 같은 inheritance/`active_round.state == "VERIFY_PENDING"` 경계를 유지하는지 다시 고정했습니다.
  - `test_supervisor_skips_run_id_inheritance_when_current_run_owner_pid_is_missing`을 추가해, owner 필드가 없는 legacy pointer로는 inheritance가 절대 살아나지 않는지 negative path로 잡았습니다.
  - `test_supervisor_skips_run_id_inheritance_when_current_run_owner_pid_mismatches_live_watcher`를 추가해, `current_run.json`이 다른 pid를 owner로 적었으면 live watcher가 살아 있어도 supervisor가 fresh `run_id`로 fall through하는지 잡았습니다.
  - `test_supervisor_write_current_run_pointer_records_live_watcher_pid`를 추가해, supervisor가 `current_run.json`을 갱신할 때 `watcher_pid` 필드에 live `experimental.pid`를 그대로 기록하는지 직접 잡았습니다.
- `.pipeline/README.md`
  - 직전 라운드의 양방향 ownership 항목 다음에 한 문장을 추가해, "supervisor는 `current_run.json`의 `watcher_pid`가 live `experimental.pid`와 정확히 같을 때만 prior `run_id`를 이어받고, owner 필드가 없거나 mismatched이거나 pid가 죽었으면 fresh `_make_run_id()`가 그대로 이긴다"는 좁은 owner-match 계약을 같이 적었습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_inherits_run_id_when_watcher_is_alive_so_status_follows_verify_replay tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_watcher_pid_is_dead tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_current_run_owner_pid_is_missing tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_current_run_owner_pid_mismatches_live_watcher tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_write_current_run_pointer_records_live_watcher_pid`
  - 결과: `Ran 5 tests`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 78 tests`, `OK`
- `python3 -m unittest -v tests.test_watcher_core.VerifyCompletionContractTest.test_poll_replays_current_run_verify_pending_even_when_latest_work_is_already_verified`
  - 결과: `Ran 1 test`, `OK`
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
  - 결과: 통과
- live tmux restart/replay 시 owner-match가 실제 분기되는지는 이번 라운드에서 다시 돌리지 않았습니다. 이유는 이번 변경이 `current_run.json` payload와 supervisor inheritance helper에 한정되고, unit 5개 + full supervisor regression 78개 + 직전 라운드의 watcher replay 회귀 1개로 owner-match 분기가 직접 고정됐기 때문입니다.

## 남은 리스크
- owner-match는 pid 정수 비교만 봅니다. pid가 매우 짧은 시간 안에 다른 프로세스에 재사용되는 극단적인 경우(예: long uptime + pid wrap) 같은 pid를 가진 무관한 프로세스가 watcher 자리를 차지하면 여전히 inheritance가 살아날 수 있습니다. 다만 이번 라운드의 reproduced risk는 stale pointer가 다른 watcher와 섞이는 더 일반적인 케이스였고, 그 경계는 이번 변경으로 닫혔습니다. 더 강한 fingerprint(`pid + start_time` 등)는 다음 same-family 슬라이스에서 다룰 수 있습니다.
- supervisor가 spawn되자마자 `run()`의 `_write_current_run_pointer()` 1회는 watcher가 아직 spawn되기 전이라 `watcher_pid: 0`을 기록할 수 있습니다. 이 시점은 inheritance가 의미 없는 cold start이므로 실질 위험은 작지만, 같은 supervisor가 watcher spawn 후에는 매 `_write_status()`에서 pointer를 다시 갱신하므로 곧바로 live pid로 회복됩니다.
- launcher/controller thin client는 여전히 `current_run.json` → `runs/<run_id>/status.json`을 따라 읽고 새 `watcher_pid` 필드는 표시 contract에 영향이 없습니다. 다음 라운드에서 controller display나 docs slug 정리가 필요하면 그때 별도 슬라이스로 다루는 편이 맞습니다.
