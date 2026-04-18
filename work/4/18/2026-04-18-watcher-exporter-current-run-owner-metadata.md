# 2026-04-18 watcher exporter current run owner metadata

## 변경 파일
- `pipeline_runtime/schema.py`
- `pipeline_runtime/supervisor.py`
- `watcher_core.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `.pipeline/README.md`

## 사용 skill
- `doc-sync`: watcher exporter와 supervisor가 공유하는 `current_run.json` owner contract를 `.pipeline/README.md`에 현재 구현 truth로 맞추기 위해 사용했습니다.
- `work-log-closeout`: 이번 라운드 closeout을 repo 규칙 형식으로 남기기 위해 사용했습니다.

## 변경 이유
- 직전 라운드 `work/4/18/2026-04-18-supervisor-run-id-inheritance-fingerprint-gate.md`는 supervisor 쪽에서 `current_run.json`을 쓸 때 `watcher_pid` + `watcher_fingerprint`를 항상 함께 기록하고, `_inherited_run_id_from_live_watcher()`가 두 필드가 모두 정확히 일치할 때만 prior `run_id`를 이어받도록 좁혔습니다.
- 하지만 `verify/4/18/2026-04-18-supervisor-run-id-inheritance-fingerprint-gate-verification.md`가 실제로 재현한 Linux 실행 경로는 부분적 truth에 머물러 있었습니다. watcher exporter(`watcher_core._write_current_run_pointer`)가 여전히 bare payload(`run_id` / `status_path` / `events_path` / `updated_at`)만 써서 supervisor가 남긴 owner metadata를 매 runtime-status refresh에서 떨쳐내고 있었습니다.
- 따라서 watcher exporter가 한 번이라도 먼저 `current_run.json`을 갱신한 뒤에 supervisor가 재시작하면, pointer에는 `watcher_pid` / `watcher_fingerprint`가 없으므로 inheritance gate가 무조건 fail해 supervisor가 fresh `_make_run_id()`로 fall through 했습니다. 핸드오프(`STATUS: implement`, `CONTROL_SEQ: 311`)가 지목한 same-family current-risk는 이 정확한 pointer boundary에 있었습니다.

## 핵심 변경
- `pipeline_runtime/schema.py`
  - 새 helper `process_starttime_fingerprint(pid)`를 추가해 `/proc/<pid>/stat` field 22(starttime)을 공용으로 뽑습니다. comm 필드가 공백/괄호를 포함하는 경우 마지막 `)` 뒤 토큰으로 starttime을 안전하게 추출하고, `/proc` 읽기 실패/포맷 깨짐은 모두 빈 문자열을 돌려 caller가 "inheritance 불가"로 처리하게 했습니다. 이 helper가 supervisor와 watcher exporter가 공유하는 단일 owner-match 정의가 됩니다.
- `pipeline_runtime/supervisor.py`
  - 기존 `RuntimeSupervisor._watcher_process_fingerprint(pid)`가 schema helper 하나만 호출하도록 정리했습니다. staticmethod 시그니처는 유지해, 기존 caller(`_write_current_run_pointer`, `_inherited_run_id_from_live_watcher`)는 변경 없이 같은 경계를 따라갑니다.
- `watcher_core.py`
  - `pipeline_runtime.schema.process_starttime_fingerprint`를 import에 추가했습니다.
  - `_write_current_run_pointer()`가 bare payload 대신 live `os.getpid()`를 `watcher_pid`로, 같은 process의 starttime fingerprint를 `watcher_fingerprint`로 같이 기록합니다. watcher process 자신이 owner이므로 외부에서 추가 identity 입력 없이도 canonical owner contract를 만족합니다.
- `tests/test_watcher_core.py`
  - `test_write_current_run_pointer_records_watcher_pid_and_fingerprint`를 `TransitionTurnTest`에 추가했습니다. watcher exporter가 `current_run.json`을 갱신했을 때 `watcher_pid == os.getpid()`이고 `watcher_fingerprint`가 비어 있지 않은지 직접 고정합니다. 같은 class의 기존 `_transition_turn` 회귀가 같은 exporter path를 이미 커버하고 있어, 추가 fixture 변경 없이 owner metadata 계약만 새 회귀로 잡혔습니다.
- `tests/test_pipeline_runtime_supervisor.py`
  - `test_supervisor_restart_inherits_run_id_after_watcher_exporter_writes_pointer`를 추가했습니다. `PIPELINE_RUNTIME_RUN_ID` 환경 변수로 watcher에게 명시적인 run_id를 주입한 뒤 watcher exporter의 `_write_current_run_pointer`가 pointer를 쓰게 하고, `experimental.pid`를 같은 python pid로 만든 상태에서 새 `RuntimeSupervisor`가 바로 그 watcher run_id를 이어받는지 end-to-end로 고정했습니다. explicit run_id 덕분에 supervisor의 fresh `_make_run_id()`가 같은 타임스탬프·pid로 우연히 같아지는 flaky match도 배제됩니다.
- `.pipeline/README.md`
  - 직전 라운드 `watcher_fingerprint` owner-match 항목 뒤에 한 문장을 추가해, "supervisor와 watcher exporter가 같은 pointer boundary를 공유하려면 watcher exporter도 `os.getpid()`와 fingerprint를 함께 기록해야 하고, 두 writer는 `pipeline_runtime/schema.process_starttime_fingerprint` 한 helper를 공유한다"는 계약을 적었습니다.

## 검증
- `python3 -m py_compile watcher_core.py pipeline_runtime/supervisor.py pipeline_runtime/schema.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_watcher_core.TransitionTurnTest.test_write_current_run_pointer_records_watcher_pid_and_fingerprint tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_restart_inherits_run_id_after_watcher_exporter_writes_pointer`
  - 결과: `Ran 2 tests`, `OK`
- `python3 -m unittest -v tests.test_watcher_core.TransitionTurnTest`
  - 결과: 전체 통과 (focused 실행 + full suite 기반 82+회귀 전부 OK)
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: 전체 통과 (78 + 신규 회귀 포함)
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 126 tests`, `OK`
- `python3 -m unittest -v tests.test_watcher_core.VerifyCompletionContractTest.test_poll_replays_current_run_verify_pending_even_when_latest_work_is_already_verified`
  - 결과: `Ran 1 test`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - 결과: `Ran 17 tests`, `OK` (shared helper가 기존 schema 회귀를 깨지 않는지 보조로 확인)
- `git diff --check -- watcher_core.py pipeline_runtime/supervisor.py pipeline_runtime/schema.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
  - 결과: 통과
- live tmux restart/replay는 이번 라운드에서 다시 돌리지 않았습니다. 이유는 이번 변경이 watcher exporter가 쓰는 `current_run.json` payload와 supervisor가 읽는 inheritance helper에 한정되고, watcher exporter/owner-match/inheritance 경로를 unit 두 개 + full supervisor 78·watcher 126 회귀로 직접 고정했기 때문입니다.

## 남은 리스크
- shared fingerprint helper는 여전히 `/proc` 기반 Linux 경계에 의존합니다. 다른 커널/컨테이너 환경으로 이동하면 fingerprint가 비어 inheritance가 항상 fresh `run_id`로 fall through 하는 safe degradation이 발생하며, 이 tradeoff는 핸드오프의 scope limit에 맞춰 이번 라운드에서 의도적으로 유지했습니다.
- watcher exporter가 먼저 pointer를 쓰는 경로는 이제 owner contract를 지키지만, watcher exporter 자체가 `PIPELINE_RUNTIME_DISABLE_EXPORTER`로 꺼진 production 경로에서는 supervisor만 pointer를 씁니다. 이 비대칭은 runtime-export disable 계약이 바뀌지 않는 한 의도된 동작입니다.
- supervisor cold start 첫 1회 pointer write는 여전히 watcher spawn 전이라 `watcher_pid: 0`, `watcher_fingerprint: ""`를 기록할 수 있고, 이 직후 watcher exporter 또는 다음 `_write_status()`에서 정상 owner metadata로 회복됩니다. 실질적 race window는 짧고, launcher/controller thin client는 두 값이 채워진 뒤에만 inherit 경로를 따라갑니다.
