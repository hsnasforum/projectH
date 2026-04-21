# 2026-04-20 emit payload date_key

## 변경 파일
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`

## 사용 skill
- `onboard-lite`: handoff, 직전 `/work`·`/verify`, target owner boundary와 검증 entrypoint를 다시 읽고 이번 slice가 exact하게 actionable한지 확인했습니다.
- `finalize-lite`: 실제 실행한 focused rerun, module regression, grep, `git diff --check` 결과만 기준으로 이번 구현 라운드의 wrap-up truth와 doc-sync 필요 여부를 정리했습니다.
- `work-log-closeout`: projectH 표준 `/work` 형식으로 이번 bounded slice closeout을 남겼습니다.

## 변경 이유
- seq 533 `dispatch_selection` event payload는 `latest_work` / `latest_verify` 두 키만 내보내고 있어, seq 543 monotonic test와 후속 consumer는 `Path(payload["latest_work"]).name[:10]`로 다시 `date_key`를 파싱해야 했습니다.
- 이번 라운드는 Gemini 551 조언을 좁게 따라, `_build_artifacts` emit payload에 `date_key` 한 키만 additive하게 넣어 seq 542 typo family를 payload source 쪽에서 일부 닫는 것이 목적이었습니다.
- handoff 제약에 따라 이 payload 변경은 같은 라운드에서 seq 533 sibling equality assertion과 seq 543 monotonic consistency assertion을 함께 갱신해야 했고, return dict는 그대로 유지해야 했습니다.

## 핵심 변경
- `pipeline_runtime/supervisor.py::_build_artifacts`의 `dispatch_selection` emit payload는 이제 2 keys에서 3 keys로 늘어났습니다. 기존 `"latest_work"`와 `"latest_verify"`는 byte-for-byte 유지하고, 새 `"date_key"`는 `work_rel`이 비어 있거나 `"—"`면 `""`, 그 외에는 `Path(work_rel).name[:10]`으로 한 번만 계산해 emit합니다.
- `_build_artifacts`의 return dict(`latest_work` / `latest_verify` path+mtime 구조)는 바꾸지 않았습니다. 이번 라운드에서 커진 것은 emitted event payload뿐입니다.
- `tests/test_pipeline_runtime_supervisor.py::test_build_artifacts_emits_dispatch_selection_event`의 seq 533 sibling equality block은 새 payload shape에 맞춰 `"date_key": "2026-04-20"`를 포함하도록 확장했습니다.
- 같은 파일의 `test_build_artifacts_dispatch_selection_event_sequence_is_monotonic_nondecreasing`에는 기존 `date_keys`/`len(dispatch_events)`/sorted-ordering assertions를 건드리지 않고, 각 event마다 `payload["date_key"] == Path(payload["latest_work"]).name[:10]`를 확인하는 additive loop만 추가했습니다. 이 loop로 emit-vs-parse consistency를 직접 잠갔습니다.
- Gemini 551 조언은 좁게 따랐습니다. seq 550 option list에 있던 4-key bundle(`latest_work_mtime`, `latest_verify_date_key`, `latest_verify_mtime`)은 이번 라운드에 추가하지 않았습니다.
- source edit는 handoff가 허용한 두 파일에만 한정했습니다. `pipeline_runtime/schema.py`, `pipeline_runtime/control_writers.py`, `pipeline_runtime/operator_autonomy.py`, `watcher_core.py`, `verify_fsm.py`, `storage/sqlite_store.py`, `scripts/pipeline_runtime_gate.py`, `.pipeline/operator_request.md`는 건드리지 않았고, seq 527 / 530 / 533 / 536 / 539 / 543 / 546 / 549 contracts는 seq 533 / seq 543 test 보강 두 군데를 제외하면 byte-for-byte 유지했습니다.
- UI, approval payload, agent/skill/config surface는 바뀌지 않아 이번 라운드 doc-sync는 필요하지 않았습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, exit 0
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_emits_dispatch_selection_event`
  - 결과: `Ran 1 test in 0.009s`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_dispatch_selection_event_sequence_is_monotonic_nondecreasing`
  - 결과: `Ran 1 test in 0.007s`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor -k build_artifacts`
  - 결과: `Ran 5 tests in 0.031s`, `OK`
  - handoff 예상은 4건이었지만, 현재 dirty-worktree baseline에는 `test_build_artifacts_prefers_manifest_feedback_path_over_verify_body_scan`까지 함께 잡혀 총 5건이 실행됐고 모두 통과했습니다.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 98 tests in 0.756s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_control_writers`
  - 결과: `Ran 7 tests in 0.011s`, `OK`
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과: `Ran 6 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - 결과: `Ran 36 tests in 0.078s`, `OK`
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 143 tests in 7.345s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 46 tests in 0.100s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.019s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.074s`, `OK`
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, 통과
- grep 결과
  - `rg -n '"dispatch_selection"' pipeline_runtime/supervisor.py`
    - 결과: `868` 총 1건
  - `rg -n '"date_key"' pipeline_runtime/supervisor.py`
    - 결과: `872` 총 1건
  - `rg -n 'work_date_key' pipeline_runtime/supervisor.py`
    - 결과: `864`, `866`, `872` 총 3건
    - handoff 예상 2건과 다르게 assignment 1건, derived assignment 1건, payload value 1건까지 총 3건이 잡혔습니다.
  - `rg -n '"date_key"' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `340`, `391` 총 2건
  - `rg -n 'def test_build_artifacts' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `190`, `222`, `253`, `305`, `345` 총 5건
    - handoff 예상 4건과 다르게 기존 `test_build_artifacts_prefers_manifest_feedback_path_over_verify_body_scan`가 포함된 현재 baseline 5건이 유지됐습니다.
  - `rg -n 'def test_' tests/test_pipeline_runtime_supervisor.py | wc -l`
    - 결과: `98`
  - `rg -n 'candidate_count|latest_any' pipeline_runtime/schema.py`
    - 결과: 총 0건
  - `rg -n 'date_key' pipeline_runtime/schema.py`
    - 결과: `290`, `291`, `293` 총 3건
  - `rg -n 'Path\(.*\)\.name\[:10\]' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `378`, `392` 총 2건

## 남은 리스크
- AXIS-EMIT-PAYLOAD-ENRICH는 이번 라운드로 부분 closure 상태입니다. `date_key`는 이제 payload source에서 한 번만 계산되어 emit되지만, 남은 optional keys(`latest_work_mtime`, `latest_verify_date_key`, `latest_verify_mtime`)는 필요 시 future round 후보로 남아 있습니다.
- AXIS-STALE-REFERENCE-AUDIT는 여전히 열린 후보입니다.
- AXIS-G7-AUTONOMY-PRODUCER는 여전히 열린 후보입니다.
- AXIS-DISPATCHER-TRACE-BACKFILL도 여전히 열린 후보입니다.
- G4, G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3는 계속 deferred 상태입니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 이번 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 0입니다.
- broad dirty worktree는 그대로 두었고, 이번 라운드 source edit는 target 2파일만 건드렸습니다. `.pipeline/operator_request.md` seq 521 canonical literals과 다른 dirty files는 untouched 상태를 유지했습니다.
