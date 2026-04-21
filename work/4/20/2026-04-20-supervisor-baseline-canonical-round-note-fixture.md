# 2026-04-20 supervisor baseline canonical round note fixture

## 변경 파일
- `tests/test_pipeline_runtime_supervisor.py`

## 사용 skill
- `onboard-lite`: 최신 handoff, 오늘자 `/work`, 대상 supervisor/schema/test 경계와 실행해야 할 검증 범위를 먼저 확인했습니다.
- `finalize-lite`: 실제 실행한 grep/unit test/diff 결과만 기준으로 이번 단일 테스트 픽스의 verification truth와 closeout readiness를 정리했습니다.
- `work-log-closeout`: projectH 표준 `/work` 형식에 맞춰 이번 구현 라운드의 변경/검증/잔여 리스크를 정리했습니다.

## 변경 이유
- `CONTROL_SEQ: 536` handoff는 AXIS-SUPERVISOR-BASELINE 범위를 production 수정 없이 `test_build_artifacts_uses_canonical_round_notes_only` 1건의 fixture truth-sync로만 좁혔습니다.
- seq 527 `latest_verify_note_for_work`는 verify note가 대응하는 work note를 명시적으로 참조해야 canonical pair로 간주합니다.
- 기존 fixture의 `verify_note.write_text("# verify\n", ...)`는 그 참조를 만들지 못해, README보다 최신 mtime을 주더라도 canonical verify note로 선택되지 않는 stale setup이었습니다.

## 핵심 변경
- [tests/test_pipeline_runtime_supervisor.py](/home/xpdlqj/code/projectH/tests/test_pipeline_runtime_supervisor.py#L190) `test_build_artifacts_uses_canonical_round_notes_only` 안에서 한 줄짜리 `verify_note.write_text("# verify\n", encoding="utf-8")`를 아래 multi-line call로만 교체했습니다.
  - `"Based on \`work/4/16/2026-04-16-real-round.md\`\n"`
- 변경 위치는 [tests/test_pipeline_runtime_supervisor.py](/home/xpdlqj/code/projectH/tests/test_pipeline_runtime_supervisor.py#L203)이며, setup/mkdir/README fixture/`os.utime`/`_build_artifacts` 호출/assertion은 그대로 유지했습니다.
- 이 fixture는 이제 seq 527 reference 규칙을 만족하면서도, README 쪽에 더 최신 mtime을 주는 기존 구성을 유지해 seq 530 `latest_round_markdown`이 README가 아니라 canonical round note만 고르는지 계속 검증합니다.
- 편집하지 않은 파일:
  - `pipeline_runtime/schema.py`
  - `pipeline_runtime/supervisor.py`
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
  - `tests/test_smoke.py`
- seq 527 `latest_verify_note_for_work`, seq 530 `latest_round_markdown`, seq 533 `_build_artifacts`의 `dispatch_selection` emit은 byte-for-byte 유지했습니다.

## 검증
- grep 확인
  - `rg -n 'def test_build_artifacts_uses_canonical_round_notes_only' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `190` 1건
  - `rg -n 'Based on .work/4/16/2026-04-16-real-round.md.' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `204` 1건
  - `rg -n 'verify_note.write_text' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `203`, `262` 총 2건
  - `rg -n 'def test_slot_verify_manifest_role_is_accepted_for_receipt' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `1063` 1건
  - `rg -n 'def test_write_status_emits_receipt_and_control_block' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `292` 1건
  - `rg -n 'def test_' tests/test_pipeline_runtime_supervisor.py`
    - 결과: 총 94건
  - `rg -n 'dispatch_selection' pipeline_runtime/supervisor.py`
    - 결과: `820` 1건
  - `rg -n 'candidate_count|latest_any' pipeline_runtime/schema.py`
    - 결과: 0건
  - `rg -n 'date_key' pipeline_runtime/schema.py`
    - 결과: `290`, `291`, `293` 총 3건
- `python3 -m py_compile tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_uses_canonical_round_notes_only`
  - 결과: `Ran 1 test in 0.009s`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor -k build_artifacts`
  - 결과: `Ran 3 tests in 0.020s`, `OK`
  - 포함 테스트:
    - `test_build_artifacts_emits_dispatch_selection_event`
    - `test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify`
    - `test_build_artifacts_uses_canonical_round_notes_only`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 94 tests in 0.704s`, `FAILED (failures=2)`
  - 남은 실패:
    - `test_slot_verify_manifest_role_is_accepted_for_receipt`: `AssertionError: 'DEGRADED' != 'STOPPED'`
    - `test_write_status_emits_receipt_and_control_block`: `AssertionError: '' is not true`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_receipt_uses_verify_matching_job_work tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_marks_receipt_verify_missing_when_only_unrelated_verify_exists`
  - 결과: `Ran 3 tests in 0.066s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - 결과: `Ran 36 tests in 0.098s`, `OK`
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과: `Ran 6 tests in 0.002s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 46 tests in 0.129s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.032s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.098s`, `OK`
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 143 tests in 7.530s`, `OK`
- `git diff --check -- tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, 통과

## 남은 리스크
- 이번 라운드는 supervisor baseline failure 3건 중 1건만 닫았습니다. 아래 2건은 그대로 남아 있고, handoff 범위를 넘기지 않기 위해 건드리지 않았습니다.
  - `test_slot_verify_manifest_role_is_accepted_for_receipt`: `DEGRADED != STOPPED`
  - `test_write_status_emits_receipt_and_control_block`: `'' is not true`
- 이번 수정은 fixture truth-sync에 국한됩니다. 다른 test-side consumer가 같은 stale assert/fixture 패턴을 아직 더 갖고 있는지는 별도 확인이 필요합니다.
- seq 527/530/533 production schema/supervisor contract는 유지됐고, production behavior change는 없습니다.
- G7-gate-blocking, G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3와 AXIS-OBSERVE-EVALUATE는 계속 defer 상태입니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 이번 범위 밖이라 그대로 남아 있습니다.
- 오늘 docs-only round count는 0입니다. 이번 round는 unit test fixture 1건만 수정했습니다.
- dirty worktree의 다른 변경은 건드리지 않았고, `pipeline_runtime/schema.py:24` 주변의 pre-existing label rename diff도 그대로 남겨 두었습니다.
