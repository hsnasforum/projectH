# 2026-04-20 dispatch selection monotonic replay

## 변경 파일
- `tests/test_pipeline_runtime_supervisor.py`

## 사용 skill
- `finalize-lite`: 실제 실행한 grep/unit test/diff 결과만 기준으로 이번 replay test 추가 라운드의 verification truth와 doc-sync 필요 여부를 정리했습니다.
- `work-log-closeout`: projectH 표준 `/work` 형식에 맞춰 변경점, 검증, 남은 리스크를 closeout으로 정리했습니다.

## 변경 이유
- seq 542 implement round는 handoff가 `event["payload"]["latest_work"][:10]`를 직접 잘라 `YYYY-MM-DD`를 뽑는다고 가정해 blocked 되었습니다. 실제 emit payload의 `latest_work`는 `4/18/2026-04-18-older-round.md`처럼 `<month>/<day>/<filename>.md` 상대경로라서, 그 표현식은 `"4/18/2026-"`만 만들었습니다.
- seq 543 handoff는 이 handoff-side typo만 복구했습니다. `Path(event["payload"]["latest_work"]).name[:10]`로 basename에서 `YYYY-MM-DD`를 자르도록 바꾸면, seq 530 `latest_round_markdown`의 `candidate.name[:10]` semantic과 정확히 맞습니다.
- 이번 slice의 목적은 Gemini 541의 `eval/dispatcher_integrity.py` 의도를 기존 `tests/` 경계 안의 replay test 하나로 옮겨, seq 533 `dispatch_selection` event stream에서 monotonic-nondecreasing ordering을 실제로 증명하는 것이었습니다.

## 핵심 변경
- [tests/test_pipeline_runtime_supervisor.py](/home/xpdlqj/code/projectH/tests/test_pipeline_runtime_supervisor.py#L344)에 `test_build_artifacts_dispatch_selection_event_sequence_is_monotonic_nondecreasing` 메서드 1개를 추가했습니다.
- handoff-relative placement은 seq 533 sibling 뒤, seq 539 fixture 앞을 유지했습니다. 현재 dirty worktree 기준 실제 위치는 [tests/test_pipeline_runtime_supervisor.py](/home/xpdlqj/code/projectH/tests/test_pipeline_runtime_supervisor.py#L305) `test_build_artifacts_emits_dispatch_selection_event` 바로 뒤와 [tests/test_pipeline_runtime_supervisor.py](/home/xpdlqj/code/projectH/tests/test_pipeline_runtime_supervisor.py#L388) `test_write_status_emits_receipt_and_control_block` 바로 앞입니다.
- 새 테스트는 `work/4/18/2026-04-18-older-round.md`를 먼저 만들고 `_build_artifacts()`를 한 번 호출한 뒤, `work/4/20/2026-04-20-newer-round.md`를 더 오래된 `mtime`으로 만들고 `_build_artifacts()`를 다시 호출합니다. 이후 `supervisor.events_path`의 `dispatch_selection` event 두 개를 읽어 `Path(event["payload"]["latest_work"]).name[:10]`으로 `date_keys`를 추출하고, `["2026-04-18", "2026-04-20"] == sorted(date_keys)`와 `len(dispatch_events) == 2`를 검증합니다.
- 이 검증으로 seq 530의 `(date_key, mtime)` comparator가 더 큰 `mtime`보다 더 새로운 날짜를 우선한다는 점과, seq 533 observability probe가 supervisor event stream에 그 ordering을 그대로 남긴다는 점을 함께 증명했습니다.
- Gemini 541의 `eval/dispatcher_integrity.py` artifact form은 unit test로 충실하게 번역했습니다. 이번 라운드에서 `eval/dispatcher_integrity.py`는 만들지 않았고, 새 top-level directory도 만들지 않았습니다.
- 편집하지 않은 파일:
  - `pipeline_runtime/supervisor.py`
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
  - `tests/test_smoke.py`
- no production code changed. seq 527 / seq 530 / seq 533 / seq 536 / seq 539 contract는 byte-for-byte 유지했습니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474/477/480/483/486/489/495/498/501/504/507/510/513/516/517/518/519/520/521/527/530/533/536/539 shipped surfaces는 의도적으로 더 수정하지 않았습니다.
- seq 542의 `handoff_date_key_mismatch` block은 이번 seq 543 recovery로 닫혔습니다.

## 검증
- grep 확인
  - `rg -n 'def test_build_artifacts_dispatch_selection_event_sequence_is_monotonic_nondecreasing' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `344` 1건
  - `rg -n 'Path\\(event\\["payload"\\]\\["latest_work"\\]\\)\\.name\\[:10\\]' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `377` 1건
  - `rg -n 'event\\["payload"\\]\\["latest_work"\\]\\[:10\\]' tests/test_pipeline_runtime_supervisor.py`
    - 결과: 0건
  - `rg -n 'def test_build_artifacts_emits_dispatch_selection_event' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `305` 1건
  - `rg -n '2026-04-18-older-round|2026-04-20-newer-round' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `348`, `349`, `365`, `366` 총 4건
  - `rg -n 'spoofed_newer_mtime' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `360`, `361` 총 2건
  - `rg -n 'def test_' tests/test_pipeline_runtime_supervisor.py | wc -l`
    - 결과: `97`
    - handoff 기대치는 `95`였지만, 현재 dirty worktree에서는 같은 파일 안에 pre-existing 추가 `def test_`들이 더 있어 grep count는 97이었습니다. 아래 `unittest` 출력은 실제 실행 결과대로 `Ran 95`를 기록했습니다.
  - `rg -n 'dispatch_selection' pipeline_runtime/supervisor.py`
    - 결과: `864` 1건
  - `rg -n 'candidate_count|latest_any' pipeline_runtime/schema.py`
    - 결과: 0건
  - `rg -n 'date_key' pipeline_runtime/schema.py`
    - 결과: `290`, `291`, `293` 총 3건
  - `ls eval/ 2>/dev/null || echo "no eval dir"`
    - 결과: existing pre-existing `eval/` directory contents
      - `__init__.py`
      - `__pycache__`
      - `harness.py`
      - `metrics.py`
      - `report.py`
      - `results`
      - `scenarios.py`
    - 이번 라운드에서 `eval/dispatcher_integrity.py`는 만들지 않았습니다.
- seq 536 / seq 539 fixture preservation spot-check
  - `rg -n 'Based on .work/4/11/work-note.md.' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `450`, `1308` 총 2건
  - `rg -n 'Based on .work/4/16/2026-04-16-real-round.md.' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `204` 1건
- `python3 -m py_compile tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_dispatch_selection_event_sequence_is_monotonic_nondecreasing`
  - 결과: `Ran 1 test in 0.008s`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor -k build_artifacts`
  - 결과: `Ran 4 tests in 0.056s`, `OK`
  - 포함 테스트:
    - `test_build_artifacts_dispatch_selection_event_sequence_is_monotonic_nondecreasing`
    - `test_build_artifacts_emits_dispatch_selection_event`
    - `test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify`
    - `test_build_artifacts_uses_canonical_round_notes_only`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 95 tests in 0.975s`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_receipt_uses_verify_matching_job_work tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_marks_receipt_verify_missing_when_only_unrelated_verify_exists`
  - 결과: `Ran 3 tests in 0.071s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - 결과: `Ran 36 tests in 0.125s`, `OK`
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 143 tests in 7.584s`, `OK`
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과: `Ran 6 tests in 0.002s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 46 tests in 0.129s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.048s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.117s`, `OK`
- `git diff --check -- tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, 통과

## 남은 리스크
- 이번 slice로 vector 2 story는 test layer에서 닫혔습니다. date_key extraction math도 실제 emit payload shape와 맞춰졌습니다.
- seq 542 typo는 좋은 경고 신호였습니다. 앞으로 emit payload field shape에 기대는 handoff는 `pipeline_runtime/supervisor.py:_build_artifacts`의 실제 return value와 sibling test literal assertion을 먼저 대조해야 합니다.
- AXIS-STALE-REFERENCE-AUDIT (`tests/test_pipeline_runtime_supervisor.py`의 bare `"# verify\n"` fixture 계열과 다른 `latest_verify_note_for_work` consumers)는 여전히 후속 후보입니다.
- G7-gate-blocking, G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3는 계속 defer 상태입니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 이번 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 0입니다. 이번 slice는 unit-test only입니다.
- dirty worktree의 다른 파일은 건드리지 않았고, 이번 라운드 쓰기 범위도 `tests/test_pipeline_runtime_supervisor.py` 1개와 이 `/work` note 1개로 제한했습니다.
