# 2026-04-18 supervisor run_id inheritance fingerprint gate

## 변경 파일
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `.pipeline/README.md`

## 사용 skill
- `doc-sync`: watcher process fingerprint 게이트 계약을 `.pipeline/README.md`에 현재 구현 truth로 맞추기 위해 사용했습니다.
- `work-log-closeout`: 이번 라운드 closeout을 repo 규칙 형식으로 남기기 위해 사용했습니다.

## 변경 이유
- 직전 라운드 `work/4/18/2026-04-18-supervisor-run-id-inheritance-owner-pid-gate.md`와 `verify/4/18/2026-04-18-supervisor-run-id-inheritance-owner-pid-gate-verification.md`는 supervisor `run_id` inheritance를 `watcher_pid` 정수 일치로 한 번 좁혔지만, 같은 pid가 매우 짧은 시간 안에 다른 process로 재사용되는 극단 케이스(예: long uptime + pid wrap)에서는 여전히 잘못된 prior `run_id`를 이어받을 수 있다는 리스크가 남아 있었습니다.
- 핸드오프(`STATUS: implement`, `CONTROL_SEQ: 310`)가 지목한 same-family current-risk는 명확합니다. supervisor가 같은 inheritance 경계에서 watcher process의 instance fingerprint까지 보지 않으면, 최근 두 라운드로 닫은 canonical runtime ownership 경계가 pid reuse 하나만으로 뚫릴 수 있었습니다.
- 그래서 이번 슬라이스에서는 pointer `watcher_pid`가 live `experimental.pid`와 같더라도, 같은 process instance 임을 증명하는 watcher fingerprint(`/proc/<pid>/stat`의 starttime)까지 같을 때만 inheritance를 허용하도록 한 단계 더 좁혔습니다.

## 핵심 변경
- `pipeline_runtime/supervisor.py`
  - 정적 helper `_watcher_process_fingerprint(pid)`를 추가해 `/proc/<pid>/stat`에서 field 22(starttime)를 안전하게 뽑습니다. comm field가 공백/괄호를 포함할 수 있어 파일의 마지막 `)` 뒤를 잘라 나머지 토큰으로 starttime을 추출하고, `/proc`이 없거나 읽기 실패면 빈 문자열을 돌려 inheritance가 fresh `_make_run_id()`로 fall through 되게 둡니다.
  - `_write_current_run_pointer()`가 매 갱신에서 live `experimental.pid`와 그 fingerprint를 동시에 기록하도록 `current_run.json`에 `watcher_fingerprint` 필드를 추가했습니다. watcher가 아직 살아 있지 않거나 fingerprint를 읽지 못하면 빈 문자열이 들어가, 그 pointer로는 이후 어떤 supervisor도 inheritance가 살아나지 않습니다.
  - `_inherited_run_id_from_live_watcher()`는 이제 (a) live `experimental.pid`와 (b) pointer `watcher_pid` 일치, (c) live fingerprint 존재, (d) pointer `watcher_fingerprint`와 live fingerprint 정확히 같음, 의 네 조건을 모두 통과해야만 prior `run_id`를 돌립니다. 그 외 모든 경우(파일 없음, pid 죽음, owner/fingerprint 필드 누락, 값 mismatch, `/proc` 접근 실패 등)는 빈 문자열을 돌려 fresh `_make_run_id()`가 그대로 이깁니다.
- `tests/test_pipeline_runtime_supervisor.py`
  - 테스트 픽스처가 supervisor helper와 같은 방식으로 fingerprint를 계산할 수 있도록, `/proc/<pid>/stat`의 starttime을 읽는 모듈-레벨 helper `_read_proc_starttime_fingerprint(pid)`를 추가했습니다.
  - 기존 positive 회귀 `test_supervisor_inherits_run_id_when_watcher_is_alive_so_status_follows_verify_replay`의 `current_run.json` fixture에 `watcher_fingerprint: _read_proc_starttime_fingerprint(os.getpid())`를 같이 넣어, 새 fingerprint-match 계약 아래에서도 같은 inheritance/`active_round.state == "VERIFY_PENDING"` 경계를 유지하는지 다시 고정했습니다.
  - 기존 `test_supervisor_skips_run_id_inheritance_when_current_run_owner_pid_mismatches_live_watcher` 픽스처에도 matching fingerprint를 넣어, 이 테스트가 pid mismatch 단독으로도 inheritance를 막는지 그대로 확인되게 했습니다.
  - `test_supervisor_skips_run_id_inheritance_when_pointer_fingerprint_is_missing`을 추가해, pid가 정확히 일치해도 pointer에 `watcher_fingerprint`가 없으면 inheritance가 절대 살아나지 않는지 고정했습니다.
  - `test_supervisor_skips_run_id_inheritance_when_pointer_fingerprint_mismatches_live_watcher`를 추가해, pointer가 같은 pid지만 stale fingerprint를 주장할 때도 supervisor가 fresh `run_id`로 fall through 하는지 pid-reuse 시나리오를 직접 재현했습니다.
  - `test_supervisor_write_current_run_pointer_records_live_watcher_fingerprint`를 추가해, supervisor가 `current_run.json`을 갱신할 때 `watcher_fingerprint` 필드에 현재 live `experimental.pid`의 `/proc` starttime을 그대로 기록하는지 직접 잡았습니다.
- `.pipeline/README.md`
  - 직전 라운드의 `watcher_pid` owner-match 항목 다음에 한 문장을 추가해, "같은 갱신에서 `/proc/<pid>/stat` starttime을 `watcher_fingerprint`로 기록하고, inheritance는 pointer `watcher_fingerprint`가 live watcher fingerprint와 정확히 같을 때만 허용한다. 필드가 없거나 mismatched이거나 `/proc`에서 읽을 수 없으면 fresh `_make_run_id()`가 이긴다"는 계약을 적었습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_inherits_run_id_when_watcher_is_alive_so_status_follows_verify_replay tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_watcher_pid_is_dead tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_current_run_owner_pid_is_missing tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_current_run_owner_pid_mismatches_live_watcher tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_pointer_fingerprint_is_missing tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_pointer_fingerprint_mismatches_live_watcher tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_write_current_run_pointer_records_live_watcher_pid tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_write_current_run_pointer_records_live_watcher_fingerprint`
  - 결과: `Ran 8 tests`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 81 tests`, `OK`
- `python3 -m unittest -v tests.test_watcher_core.VerifyCompletionContractTest.test_poll_replays_current_run_verify_pending_even_when_latest_work_is_already_verified`
  - 결과: `Ran 1 test`, `OK`
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
  - 결과: 통과
- live tmux restart/replay에서 fingerprint mismatch 분기가 실제 코드 경로로 돌았는지는 이번 라운드에서 다시 돌리지 않았습니다. 이유는 이번 변경이 `current_run.json` payload와 supervisor inheritance helper 내부에 한정되고, unit 8개 + full supervisor regression 81개 + 직전 라운드의 watcher replay 회귀 1개로 pid/fingerprint 분기가 직접 고정됐기 때문입니다.

## 남은 리스크
- fingerprint source는 `/proc/<pid>/stat`의 starttime 하나입니다. `/proc`이 제공되지 않는 환경(예: 비-Linux)에서는 fingerprint가 빈 문자열이 되어 inheritance가 항상 fresh `_make_run_id()`로 fall through 합니다. 이 tradeoff는 safe fallback이라 이번 라운드에서는 그대로 두었고, 필요하면 다음 슬라이스에서 container-aware 대체 경로를 더 좁게 붙일 수 있습니다.
- supervisor cold-start 첫 1회 pointer write는 watcher가 아직 spawn되기 전이라 `watcher_pid: 0`, `watcher_fingerprint: ""`가 기록될 수 있습니다. 이 시점의 pointer로는 어떤 supervisor도 inheritance를 살리지 못하므로 안전하고, watcher spawn 직후 매 `_write_status()`에서 pointer가 live pid + fingerprint로 즉시 갱신됩니다.
- 장기적으로는 watcher 자신이 `current_run.json`에 owner identity를 적는 방향이 더 좁지만, 이번 라운드의 scope limit은 supervisor-managed pointer 한 곳에 한정됐기 때문에 그 경로는 별도 follow-up으로 남겨둡니다.
