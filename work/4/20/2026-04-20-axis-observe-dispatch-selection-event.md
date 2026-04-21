# 2026-04-20 axis observe dispatch selection event

## 변경 파일
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`

## 사용 skill
- `onboard-lite`: 최신 handoff, `/work`, `/verify`, Gemini arbitration, 대상 helper/test 경계를 짧게 확인했습니다.
- `finalize-lite`: 실제 실행한 grep/unit test/diff 결과를 기준으로 observability slice의 verification truth, doc-sync triage, `/work` closeout readiness를 함께 정리했습니다.

## 변경 이유
- seq 527과 seq 530이 schema layer에서 dispatcher-repoint defect vector 1+2를 닫았지만, 실제 dispatcher가 그 뒤 아직 재호출되지 않아 empirical confirmation 경로가 없었습니다.
- Gemini 532는 behavior를 더 바꾸지 말고 `RuntimeSupervisor._build_artifacts`의 기존 event stream에 `(latest_work, latest_verify)` selection을 남기는 AXIS-OBSERVE를 정확한 다음 slice로 pin했습니다.
- 이번 라운드는 observability만 추가하고, supervisor의 return contract와 기존 schema contract는 그대로 유지하는 것이 목적입니다.

## 핵심 변경
- `pipeline_runtime/supervisor.py:819-822`에 `self._append_event("dispatch_selection", {"latest_work": work_rel, "latest_verify": verify_rel})` 호출을 정확히 1개 삽입했습니다.
  - 위치는 `_build_artifacts`의 `if work_rel != "—":` branch와 `else:` branch가 모두 끝난 뒤, `return` 직전입니다.
  - 따라서 `work_rel != "—"` 경로와 `"—"` fallback 경로 모두에서 emit이 정확히 한 번만 발생합니다.
- `_build_artifacts`의 반환 dict shape는 그대로 유지했습니다.
  - `{"latest_work": {"path": work_rel, "mtime": work_mtime}, "latest_verify": {"path": verify_rel, "mtime": verify_mtime}}`
  - 그래서 `pipeline_runtime/supervisor.py` downstream call sites와 return value를 assert하는 기존 테스트 의미는 바뀌지 않았습니다.
- `tests/test_pipeline_runtime_supervisor.py:250-287`에 `test_build_artifacts_emits_dispatch_selection_event`를 추가했습니다.
  - 위치는 `test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify` 바로 뒤입니다.
  - 패턴은 기존 event-stream test들이 쓰는 방식과 같이 `supervisor.events_path.read_text(...).splitlines()` + `json.loads(line)`로 JSONL을 읽어 `dispatch_selection` event 하나와 payload를 확인합니다.
  - fixture는 `work/4/20/2026-04-20-observable-round.md`와 `verify/4/20/2026-04-20-observable-verify.md`를 만들고, verify note가 work note를 explicit reference하는 최소 shape입니다.
- 3개의 pre-existing supervisor baseline failure는 그대로 유지했습니다.
  - `test_build_artifacts_uses_canonical_round_notes_only`
  - `test_slot_verify_manifest_role_is_accepted_for_receipt`
  - `test_write_status_emits_receipt_and_control_block`
- 이번 round에서 편집하지 않은 파일:
  - `pipeline_runtime/schema.py`
  - `watcher_core.py`
  - `verify_fsm.py`
  - `scripts/pipeline_runtime_gate.py`
  - `storage/sqlite_store.py`
  - `.pipeline/operator_request.md`
  - `.pipeline/gemini_request.md`
  - `.pipeline/gemini_advice.md`
  - `tests/test_pipeline_runtime_schema.py`
  - `tests/test_watcher_core.py`
  - `tests/test_operator_request_schema.py`
  - `tests/test_pipeline_gui_backend.py`
- seq 527 `latest_verify_note_for_work` contract와 seq 530 `latest_round_markdown` `(date_key, mtime)` contract는 byte-for-byte 그대로 유지했습니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474/477/480/483/486/489/495/498/501/504/507/510/513/516/517/518/519/520/521/527/530 shipped surfaces는 의도적으로 더 수정하지 않았습니다.
- doc-sync triage 결과 없음: 이번 변경은 supervisor observability emit과 unit test 1개 추가만 포함했고 README/docs/browser contract 변경은 없습니다.

## 검증
- grep 확인
  - `rg -n 'def _build_artifacts' pipeline_runtime/supervisor.py`
    - 결과: 1건 (`803`)
  - `rg -n 'dispatch_selection' pipeline_runtime/supervisor.py`
    - 결과: 1건 (`820`)
  - `rg -n 'self._append_event' pipeline_runtime/supervisor.py`
    - 결과: 19건
    - 신규 hit는 `819`이고, baseline 18건에서 +1 되었습니다.
  - `rg -n 'def test_build_artifacts' tests/test_pipeline_runtime_supervisor.py`
    - 결과: 3건 (`190`, `219`, `250`)
  - `rg -n 'dispatch_selection' tests/test_pipeline_runtime_supervisor.py`
    - 결과: 2건 (`250`, `277`)
  - `rg -n '2026-04-20-observable-round|2026-04-20-observable-verify' tests/test_pipeline_runtime_supervisor.py`
    - 결과: 7건 (`254`, `255`, `260`, `268`, `269`, `283`, `284`)
    - handoff 예시 4 또는 6보다 1건 더 많은 이유는 verify fixture write line의 embedded work reference string(`260`)도 함께 잡히기 때문입니다.
  - `rg -n 'def test_' tests/test_pipeline_runtime_supervisor.py`
    - 결과: 94건
  - `rg -n 'candidate_count|latest_any' pipeline_runtime/schema.py`
    - 결과: 0건
  - `rg -n 'date_key|best_date' pipeline_runtime/schema.py`
    - 결과: 4건 (`275`, `290`, `291`, `293`)
    - handoff 기대치 `>=5`와 달리 `date_key`와 `best_date`가 같은 comparator line(`291`)에 함께 있어 unique line count는 4건입니다.
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor -k build_artifacts`
  - 결과: `Ran 3 tests in 0.021s`, `FAILED (failures=1)`
  - detail:
    - `test_build_artifacts_emits_dispatch_selection_event` PASS
    - `test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify` PASS
    - `test_build_artifacts_uses_canonical_round_notes_only` FAIL
  - preserved baseline assertion message:
    - `AssertionError: '—' != '4/16/2026-04-16-real-verify.md'`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 94 tests in 0.707s`, `FAILED (failures=3)`
  - failing method names는 baseline과 동일:
    - `test_build_artifacts_uses_canonical_round_notes_only`
    - `test_slot_verify_manifest_role_is_accepted_for_receipt`
    - `test_write_status_emits_receipt_and_control_block`
  - preserved baseline assertion messages:
    - `test_build_artifacts_uses_canonical_round_notes_only`: `AssertionError: '—' != '4/16/2026-04-16-real-verify.md'`
    - `test_slot_verify_manifest_role_is_accepted_for_receipt`: `AssertionError: 'DEGRADED' != 'STOPPED'`
    - `test_write_status_emits_receipt_and_control_block`: `AssertionError: '' is not true`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_receipt_uses_verify_matching_job_work tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_marks_receipt_verify_missing_when_only_unrelated_verify_exists`
  - 결과: `Ran 3 tests in 0.065s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - 결과: `Ran 36 tests in 0.109s`, `OK`
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 143 tests in 8.541s`, `OK`
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과: `Ran 6 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 46 tests in 0.103s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.025s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.093s`, `OK`
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, 통과
- 생략한 항목
  - `tests.test_web_app`, Playwright, `make e2e-test`는 handoff 범위를 벗어난 browser/web 계약이라 실행하지 않았습니다.

## 남은 리스크
- 이번 slice는 pure observability입니다. dispatcher behavior 자체는 바꾸지 않습니다. defect vector 1+2는 이미 schema-layer contract로 닫혀 있고, 이번 emit은 다음 `/verify`가 그 패턴이 실제로 사라졌는지 경험적으로 확인하는 probe입니다.
- `_build_artifacts()`가 호출될 때마다 `self.events_path`에 JSONL line 1개가 추가됩니다. production path가 `_build_artifacts`를 hot loop로 호출하면 events file 증가 속도가 빨라질 수 있습니다. 현재 supervisor 구조에서는 status tick 단위 호출이라 기존 `control_changed`류 event와 비슷한 수준의 bounded amplification으로 보입니다.
- event payload는 상대 경로 문자열만 담고, unresolved 상태에서는 `"—"`를 사용합니다. downstream analytics가 non-empty path를 전제하면 안 됩니다.
- `tests.test_pipeline_runtime_supervisor`의 3 pre-existing baseline failure는 이번 라운드에서도 unchanged입니다. AXIS-SUPERVISOR-BASELINE은 Gemini 532가 이번 round에서 명시적으로 declined 했습니다.
- G7-gate-blocking, G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3는 계속 deferred입니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 0을 유지합니다. 이번 slice는 production Python + unit test code 변경입니다.
- dirty worktree는 이번 두 target file 외에는 untouched 상태로 두었고, `pipeline_runtime/schema.py:22-25`의 pre-existing label-rename diff도 그대로 남겨 두었습니다.
