# 2026-04-20 emit payload enrich cont

## 변경 파일
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`

## 사용 skill
- `onboard-lite`: handoff, 직전 `/work`·`/verify`, target owner boundary와 검증 entrypoint를 다시 읽고 이번 slice가 exact하게 actionable한지 확인했습니다.
- `finalize-lite`: 실제 실행한 focused rerun, module regression, grep, `git diff --check` 결과만 기준으로 이번 구현 라운드의 wrap-up truth와 doc-sync 필요 여부를 정리했습니다.
- `work-log-closeout`: projectH 표준 `/work` 형식으로 이번 bounded slice closeout을 남겼습니다.

## 변경 이유
- seq 552에서 `dispatch_selection` emit payload는 3 keys(`latest_work`, `latest_verify`, `date_key`)까지 늘어났지만, mtime pair와 verify-side `date_key`는 여전히 downstream에서 별도로 유도해야 했습니다.
- 이번 라운드는 Gemini 554가 제안한 6-key shape를 좁게 마저 닫아, `_build_artifacts` scope 안에 이미 존재하던 `work_mtime` / `verify_mtime`을 그대로 재사용하고 `verify_date_key`만 대칭 계산해 payload source에서 한 번에 emit하는 것이 목적이었습니다.
- handoff 제약에 따라 이 payload 변경은 같은 라운드에서 seq 533 sibling equality block과 seq 543 monotonic additive loop를 함께 확장해야 했고, `_build_artifacts` return dict는 그대로 유지해야 했습니다.

## 핵심 변경
- `pipeline_runtime/supervisor.py::_build_artifacts`의 `dispatch_selection` emit payload는 이제 3 keys에서 6 keys로 늘어났습니다. 기존 `latest_work`, `latest_verify`, `date_key`는 byte-for-byte 유지하고, 새 `latest_work_mtime`, `latest_verify_date_key`, `latest_verify_mtime`를 `date_key` 뒤에 지정된 순서로 append했습니다.
- `latest_work_mtime`과 `latest_verify_mtime`는 `_build_artifacts` scope에 이미 있던 `work_mtime` / `verify_mtime`를 그대로 재사용합니다. `latest_verify_date_key`는 seq 552의 `work_date_key`와 대칭으로 계산하되, `verify_rel`이 비어 있거나 `"—"`이면 `""` sentinel을 사용합니다.
- `_build_artifacts`의 return dict(`latest_work` / `latest_verify` path+mtime 구조)는 바꾸지 않았습니다. 이번 라운드에서 커진 것은 emitted event payload뿐입니다.
- `tests/test_pipeline_runtime_supervisor.py::test_build_artifacts_emits_dispatch_selection_event`의 seq 533 sibling equality block은 6-key full payload를 직접 검증하도록 확장했고, `expected_work_mtime` / `expected_verify_mtime`는 assert 직전에 `stat().st_mtime`으로 캡처해 비교하게 했습니다.
- 같은 파일의 `test_build_artifacts_dispatch_selection_event_sequence_is_monotonic_nondecreasing`의 기존 additive loop는 그대로 유지하면서, `assertAlmostEqual(payload["latest_work_mtime"], work_file.stat().st_mtime, places=3)`와 `"—"` branch lock(`latest_verify == "—"`, `latest_verify_date_key == ""`, `latest_verify_mtime == 0.0`) 세트를 추가했습니다. 이로써 emit-vs-parse consistency와 verify sentinel behavior를 함께 잠갔습니다.
- source edit는 handoff가 허용한 두 파일에만 한정했습니다. `pipeline_runtime/control_writers.py`, `pipeline_runtime/operator_autonomy.py`, `pipeline_runtime/schema.py`, `watcher_core.py`, `verify_fsm.py`, `storage/sqlite_store.py`, `scripts/pipeline_runtime_gate.py`, `.pipeline/operator_request.md`는 건드리지 않았고, seq 527 / 530 / 533 / 536 / 539 / 543 / 546 / 549 / 552 contracts는 두 테스트 확장 지점을 제외하면 byte-for-byte 유지했습니다.
- UI, approval payload, agent/skill/config surface는 바뀌지 않아 이번 라운드 doc-sync는 필요하지 않았습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, exit 0
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_emits_dispatch_selection_event`
  - 결과: `Ran 1 test in 0.008s`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_dispatch_selection_event_sequence_is_monotonic_nondecreasing`
  - 결과: `Ran 1 test in 0.012s`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor -k build_artifacts`
  - 결과: `Ran 5 tests in 0.096s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 98 tests in 1.123s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_control_writers`
  - 결과: `Ran 7 tests in 0.011s`, `OK`
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과: `Ran 6 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - 결과: `Ran 36 tests in 0.150s`, `OK`
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 143 tests in 7.431s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 46 tests in 0.173s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.033s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.095s`, `OK`
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, 통과
- grep 결과
  - `rg -n '"dispatch_selection"' pipeline_runtime/supervisor.py`
    - 결과: `871` 총 1건
  - `rg -n '"date_key"|"latest_work_mtime"|"latest_verify_date_key"|"latest_verify_mtime"' pipeline_runtime/supervisor.py`
    - 결과: `875`, `876`, `877`, `878` 총 4건
  - `rg -n 'verify_date_key' pipeline_runtime/supervisor.py`
    - 결과: `867`, `869`, `877` 총 3건
  - `rg -n 'work_mtime|verify_mtime' pipeline_runtime/supervisor.py`
    - 결과: `843`, `845`, `858`, `861`, `863`, `876`, `878`, `882`, `883` 총 9건
    - 모든 hit는 `_build_artifacts` 내부에만 있습니다. 다른 emit site는 건드리지 않았습니다.
  - `rg -n '"latest_work_mtime"|"latest_verify_date_key"|"latest_verify_mtime"' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `343`, `344`, `345`, `401`, `406`, `407` 총 6건
  - `rg -n 'latest_verify_date_key|latest_work_mtime|latest_verify_mtime' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `343`, `344`, `345`, `401`, `406`, `407` 총 6건
  - `rg -n 'assertAlmostEqual' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `400` 총 1건
  - `rg -n 'def test_build_artifacts' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `190`, `222`, `253`, `305`, `350` 총 5건
  - `rg -n 'def test_' tests/test_pipeline_runtime_supervisor.py | wc -l`
    - 결과: `98`
  - `rg -n 'candidate_count|latest_any' pipeline_runtime/schema.py`
    - 결과: 총 0건
  - `rg -n 'date_key' pipeline_runtime/schema.py`
    - 결과: `290`, `291`, `293` 총 3건

## 남은 리스크
- AXIS-EMIT-PAYLOAD-ENRICH는 이번 라운드로 Gemini 554가 제안한 6-key shape에서 닫혔습니다.
- AXIS-STALE-REFERENCE-AUDIT는 여전히 열린 후보입니다.
- AXIS-G7-AUTONOMY-PRODUCER는 여전히 열린 후보입니다.
- AXIS-DISPATCHER-TRACE-BACKFILL도 여전히 열린 후보이며, 이제 live emit이 `date_key`, mtime pair, `latest_verify_date_key`까지 모두 싣기 때문에 다음 empirical trace 확인 축이 더 또렷해졌습니다.
- G4, G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3는 계속 deferred 상태입니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 이번 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 0입니다.
- broad dirty worktree는 그대로 두었고, 이번 라운드 source edit는 target 2파일만 건드렸습니다. `.pipeline/operator_request.md` seq 521 canonical literals과 다른 dirty files는 untouched 상태를 유지했습니다.
