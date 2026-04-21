# 2026-04-20 supervisor baseline receipt fixture pair

## 변경 파일
- `tests/test_pipeline_runtime_supervisor.py`

## 사용 skill
- `finalize-lite`: 실제 실행한 grep/unit test/diff 결과만 기준으로 이번 fixture truth-sync 라운드의 verification truth와 doc-sync 필요 여부를 정리했습니다.
- `work-log-closeout`: projectH 표준 `/work` 형식에 맞춰 변경점, 실행한 검증, 남은 리스크를 한국어 closeout으로 정리했습니다.

## 변경 이유
- `CONTROL_SEQ: 539` handoff는 seq 536 이후 남아 있던 `tests.test_pipeline_runtime_supervisor` baseline failure 2건을 production 수정 없이 test-side fixture truth-sync 2건으로만 닫으라고 지정했습니다.
- 두 테스트는 모두 job-state JSON의 `artifact_path`를 `"work/4/11/work-note.md"`로 두고도 verify note body를 bare `"# verify\n"`로 써 두어, seq 527 `latest_verify_note_for_work`의 referenced-match 계약을 만족하지 못하고 있었습니다.
- 그 결과 `latest_verify_note_for_work`가 대응 verify note를 찾지 못해 receipt emission이 끊기고, 한쪽은 `last_receipt_id == ""`, 다른 한쪽은 `receipt_verify_missing` 경유 `runtime_state == "DEGRADED"`로 남아 있었습니다.

## 핵심 변경
- [tests/test_pipeline_runtime_supervisor.py](/home/xpdlqj/code/projectH/tests/test_pipeline_runtime_supervisor.py#L353)에서 `test_write_status_emits_receipt_and_control_block`의 `verify_path.write_text("# verify\n", encoding="utf-8")`를 아래 multi-line call로 교체했습니다.
  - `verify_path.write_text("Based on \`work/4/11/work-note.md\`\n", encoding="utf-8")`
- [tests/test_pipeline_runtime_supervisor.py](/home/xpdlqj/code/projectH/tests/test_pipeline_runtime_supervisor.py#L1123)에서 `test_slot_verify_manifest_role_is_accepted_for_receipt`의 `(verify_dir / "2026-04-11-verify.md").write_text("# verify\n", encoding="utf-8")`를 아래 multi-line call로 교체했습니다.
  - `(verify_dir / "2026-04-11-verify.md").write_text("Based on \`work/4/11/work-note.md\`\n", encoding="utf-8")`
- 두 replacement의 reference string은 각 테스트 job-state JSON의 `artifact_path` 값 `"work/4/11/work-note.md"`와 정확히 일치합니다.
  - `test_write_status_emits_receipt_and_control_block`: [tests/test_pipeline_runtime_supervisor.py](/home/xpdlqj/code/projectH/tests/test_pipeline_runtime_supervisor.py#L341)
  - `test_slot_verify_manifest_role_is_accepted_for_receipt`: [tests/test_pipeline_runtime_supervisor.py](/home/xpdlqj/code/projectH/tests/test_pipeline_runtime_supervisor.py#L1112)
- 이로써 `latest_verify_note_for_work`가 same-day work/verify pair를 다시 end-to-end로 해석하고, receipt emission → `last_receipt_id` truthy → `runtime_state == "STOPPED"` → `degraded_reason == ""` 연쇄가 production code 변경 없이 다시 exercised 됩니다.
- seq 536 fixture인 [tests/test_pipeline_runtime_supervisor.py](/home/xpdlqj/code/projectH/tests/test_pipeline_runtime_supervisor.py#L203) `verify_note.write_text("Based on \`work/4/16/2026-04-16-real-round.md\`\n", ...)`는 byte-for-byte 유지했고, `test_build_artifacts_uses_canonical_round_notes_only`는 계속 green입니다.
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
- seq 527 `latest_verify_note_for_work`, seq 530 `latest_round_markdown`, seq 533 `_build_artifacts`의 `dispatch_selection`, seq 536 `test_build_artifacts_uses_canonical_round_notes_only` fixture 계약은 byte-for-byte 유지했습니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474/477/480/483/486/489/495/498/501/504/507/510/513/516/517/518/519/520/521/527/530/533/536 shipped surfaces는 의도적으로 더 수정하지 않았습니다.
- doc-sync triage 결과 없음: 이번 라운드는 unit-test fixture 두 곳만 맞춘 구현 라운드라 README/docs 갱신 대상이 없었습니다.

## 검증
- grep 확인
  - `rg -n 'def test_write_status_emits_receipt_and_control_block' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `292` 1건
  - `rg -n 'def test_slot_verify_manifest_role_is_accepted_for_receipt' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `1069` 1건
  - `rg -n 'Based on .work/4/11/work-note.md.' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `354`, `1124` 총 2건
  - `rg -n 'Based on .work/4/16/2026-04-16-real-round.md.' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `204` 1건
  - `rg -n '"# verify\\\\n"' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `1057` 1건
    - 이번 라운드 시작 시 target 2건과 unrelated 1건이 bare `"# verify\n"`를 쓰고 있었고, 이번 수정 후에는 unrelated fixture 1건만 남아 총 hit 수가 2 감소했습니다.
  - `rg -n 'verify_note.write_text|verify_path.write_text|write_text\("# verify' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `203`, `262`, `353`, `546`, `547`, `1057` 총 6건
    - `203`은 seq 536 canonical fixture, `262`는 build_artifacts sibling fixture, `353`은 이번 round의 multi-line `verify_path.write_text`, `546`/`547`은 unrelated `# verify a/b`, `1057`은 manifest mismatch 계열의 남겨 둔 bare fixture입니다.
  - `rg -n 'def test_' tests/test_pipeline_runtime_supervisor.py | wc -l`
    - 결과: `94`
  - `rg -n 'dispatch_selection' pipeline_runtime/supervisor.py`
    - 결과: `820` 1건
  - `rg -n 'candidate_count|latest_any' pipeline_runtime/schema.py`
    - 결과: 0건
  - `rg -n 'date_key' pipeline_runtime/schema.py`
    - 결과: `290`, `291`, `293` 총 3건
- `python3 -m py_compile tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_emits_receipt_and_control_block`
  - 결과: `Ran 1 test in 0.035s`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_slot_verify_manifest_role_is_accepted_for_receipt`
  - 결과: `Ran 1 test in 0.093s`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor -k build_artifacts`
  - 결과: `Ran 3 tests in 0.056s`, `OK`
  - 포함 테스트:
    - `test_build_artifacts_emits_dispatch_selection_event`
    - `test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify`
    - `test_build_artifacts_uses_canonical_round_notes_only`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 94 tests in 0.851s`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_receipt_uses_verify_matching_job_work tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_marks_receipt_verify_missing_when_only_unrelated_verify_exists`
  - 결과: `Ran 3 tests in 0.093s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - 결과: `Ran 36 tests in 0.092s`, `OK`
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 143 tests in 7.525s`, `OK`
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과: `Ran 6 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 46 tests in 0.128s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.030s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.106s`, `OK`
- `git diff --check -- tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, 통과

## 남은 리스크
- 이번 slice는 3-baseline chain을 test-fixture layer에서 닫았습니다. 그렇다고 `latest_verify_note_for_work`를 소비하는 다른 test-side fixture가 모두 감사된 것은 아니므로 AXIS-STALE-REFERENCE-AUDIT는 후속 후보로 남습니다.
- seq 527/530/533 production contract는 유지됐고, production behavior change는 없습니다.
- AXIS-OBSERVE-EVALUATE와 seq 533 `dispatch_selection`의 empirical monotonic-nondecreasing test는 아직 열려 있는 후보입니다.
- G7-gate-blocking, G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3는 계속 defer 상태입니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 이번 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 0입니다. 이번 slice는 unit-test fixture만 수정했습니다.
- dirty worktree의 다른 파일은 건드리지 않았고, `pipeline_runtime/schema.py:22-25`의 pre-existing label-rename diff도 그대로 남겨 두었습니다.
