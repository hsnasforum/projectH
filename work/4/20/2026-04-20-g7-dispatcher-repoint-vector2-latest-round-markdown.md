# 2026-04-20 G7 dispatcher repoint vector2 latest_round_markdown

## 변경 파일
- `pipeline_runtime/schema.py`
- `tests/test_pipeline_runtime_schema.py`

## 사용 skill
- `onboard-lite`: 최신 handoff, `/work`, verify/operator 문맥, 대상 helper/caller 경계를 짧게 재확인했습니다.
- `finalize-lite`: 실제 실행한 grep/unit test/diff 기준으로 focused verification, doc-sync triage, `/work` closeout readiness를 함께 정리했습니다.

## 변경 이유
- seq 527이 `latest_verify_note_for_work`의 singleton fallback을 제거해 defect vector 1 (`VERIFY single-path lock-in`)을 닫은 뒤에도, seq 521에서 검증된 vector 2 (`4/18 WORK reverse-walk`)는 별도로 남아 있었습니다.
- Gemini 529 advice와 seq 530 handoff는 caller가 아니라 shared owner boundary인 `pipeline_runtime/schema.py:latest_round_markdown`에서 이 문제를 닫도록 고정했습니다.
- 이번 slice의 목적은 older-date note의 `mtime`가 더 커도 newer-date note가 선택되도록 "chronological-first selection"을 적용해 backwards-walk를 막는 것입니다.

## 핵심 변경
- `pipeline_runtime/schema.py:273-297`의 `latest_round_markdown` comparator를 `mtime` 단독 비교에서 `(date_key, mtime)` tuple 비교로 바꿨습니다.
  - 추가한 local: `best_date = ""` (`:275`)
  - 추가한 assignment: `date_key = candidate.name[:10]` (`:290`)
  - 변경한 비교식: `if (date_key, mtime) > (best_date, best_mtime):` (`:291`)
  - 추가한 update: `best_date = date_key` (`:293`)
- 반환 shape `tuple[str, float]`는 그대로 유지했습니다. 따라서 `pipeline_runtime/supervisor.py:804`와 `:818` call site는 수정 없이 계속 동작합니다.
- `tests/test_pipeline_runtime_schema.py:101-119`에 `test_latest_round_markdown_prefers_newer_date_over_newer_mtime`를 추가했습니다.
  - 위치는 `test_latest_round_markdown_ignores_root_readme` 바로 뒤, `LoadJobStatesSharedFilesTest` 앞입니다.
  - fixture shape는 `4/18/2026-04-18-older-date.md`와 `4/20/2026-04-20-newer-date.md` 두 파일을 만든 뒤, older-date file의 `mtime`를 newer-date보다 100초 크게 spoof해도 `4/20` 파일이 선택되어야 한다는 형태입니다.
- `test_latest_round_markdown_ignores_root_readme` (`tests/test_pipeline_runtime_schema.py:82-99`)는 byte-for-byte 수정하지 않았습니다.
- `LatestVerifyNoteForWorkTest` 7개 메서드와 `PathEnforcedJobStateOwnershipTest` 7개 메서드는 수정하지 않았습니다.
- 이번 round에서 편집하지 않은 파일:
  - `watcher_core.py`
  - `pipeline_runtime/supervisor.py`
  - `verify_fsm.py`
  - `scripts/pipeline_runtime_gate.py`
  - `storage/sqlite_store.py`
  - `.pipeline/operator_request.md`
  - `.pipeline/gemini_request.md`
  - `.pipeline/gemini_advice.md`
  - `tests/test_operator_request_schema.py`
  - `tests/test_pipeline_gui_backend.py`
  - `tests/test_watcher_core.py`
  - `tests/test_pipeline_runtime_supervisor.py`
- `pipeline_runtime/schema.py:22-25`의 pre-existing dirty label-rename diff는 그대로 두었습니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474/477/480/483/486/489/495/498/501/504/507/510/513/516/517/518/519/520/521/527 shipped surfaces는 의도적으로 더 수정하지 않았고, seq 527 RESOLVE-B contract (`latest_verify_note_for_work` singleton-fallback removal)는 그대로 보존했습니다.
- doc-sync triage 결과 없음: 이번 변경은 schema helper comparator와 unit test 1개 추가만 포함했고 README/docs/browser contract 변경은 없었습니다.

## 검증
- grep 확인
  - `rg -n 'def latest_round_markdown' pipeline_runtime/schema.py`
    - 결과: 1건 (`273`)
  - `rg -n 'best_date' pipeline_runtime/schema.py`
    - 결과: 3건 (`275`, `291`, `293`)
  - `rg -n 'date_key' pipeline_runtime/schema.py`
    - 결과: 3건 (`290`, `291`, `293`)
    - handoff 기대치 2와 달리 `best_date = date_key` update line까지 pattern에 잡혀 3건이 나왔습니다.
  - `rg -n 'best_mtime' pipeline_runtime/schema.py`
    - 결과: 8건 (`253`, `261`, `263`, `270`, `276`, `291`, `294`, `297`)
  - `rg -n 'ROUND_NOTE_NAME_RE' pipeline_runtime/schema.py`
    - 결과: 3건 (`32`, `284`, `343`)
  - `rg -n 'def test_latest_round_markdown_' tests/test_pipeline_runtime_schema.py`
    - 결과: 2건 (`82`, `101`)
  - `rg -n 'def test_' tests/test_pipeline_runtime_schema.py`
    - 결과: 36건
  - `rg -n '2026-04-18-older-date|2026-04-20-newer-date' tests/test_pipeline_runtime_schema.py`
    - 결과: 3건 (`104`, `105`, `118`)
    - handoff 기대치 2와 달리 fixture path 2건 + assertion string 1건이 함께 잡혀 3건입니다.
  - `rg -n 'spoofed_older_mtime' tests/test_pipeline_runtime_schema.py`
    - 결과: 2건 (`112`, `113`)
  - `rg -n 'candidate_count|latest_any' pipeline_runtime/schema.py`
    - 결과: 0건
- `python3 -m py_compile pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py`
  - 결과: 출력 없음, 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_schema -k latest_round_markdown`
  - 결과: `Ran 2 tests in 0.007s`, `OK`
  - passing methods:
    - `test_latest_round_markdown_ignores_root_readme`
    - `test_latest_round_markdown_prefers_newer_date_over_newer_mtime`
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - 결과: `Ran 36 tests in 0.131s`, `OK`
  - full-module green 안에 `LatestVerifyNoteForWorkTest` 7 green과 `PathEnforcedJobStateOwnershipTest` 7 green이 그대로 포함됩니다.
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 143 tests in 7.519s`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_receipt_uses_verify_matching_job_work tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_marks_receipt_verify_missing_when_only_unrelated_verify_exists`
  - 결과: `Ran 3 tests in 0.058s`, `OK`
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과: `Ran 6 tests in 0.002s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 46 tests in 0.105s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.023s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.077s`, `OK`
- `git diff --check -- pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py`
  - 결과: 출력 없음, 통과
- 생략한 항목
  - `tests.test_web_app`, Playwright, `make e2e-test`는 handoff 범위를 벗어난 browser/web 계약이라 실행하지 않았습니다.
  - handoff가 out-of-scope로 못 박은 `tests.test_pipeline_runtime_supervisor`의 3 pre-existing baseline failure는 고치지 않았습니다.

## 남은 리스크
- 이번 변경은 `latest_round_markdown` owner boundary에서 chronological-first selection을 강제해 defect vector 2 (`4/18 WORK reverse-walk`)를 닫습니다. seq 527의 vector 1 closure와 합치면 seq 521의 validated-bug pair는 schema layer에서 모두 대응된 상태입니다.
- 이 수정은 `ROUND_NOTE_NAME_RE`가 `YYYY-MM-DD-` filename prefix를 보장한다는 전제에 의존합니다. 앞으로 regex가 non-date-prefixed filename도 허용하도록 넓어지면 `date_key = candidate.name[:10]` 비교가 조용히 잘못될 수 있습니다. guard boundary는 `pipeline_runtime/schema.py:32`입니다.
- repo 어딘가의 dispatcher caller가 예전 "max mtime only" semantics에 의존해 older note를 touch해서 재디스패치하는 흐름을 기대했다면, 이번 slice는 그것을 숨기지 않고 test failure로 드러내는 쪽을 택했습니다. 현재는 `tests.test_watcher_core`와 supervisor matching-verify triple에서 그런 caller는 관측되지 않았습니다.
- `normalize_decision_class` / `normalize_reason_code`는 여전히 pass-through이고, 3 canonical literal의 runtime gating은 이번 slice에서 강제하지 않았습니다.
- G7-gate-blocking, G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3는 계속 deferred입니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 그대로 남아 있습니다.
- `tests.test_pipeline_runtime_supervisor`의 3 pre-existing baseline failure (`test_build_artifacts_uses_canonical_round_notes_only`, `test_slot_verify_manifest_role_is_accepted_for_receipt`, `test_write_status_emits_receipt_and_control_block`)는 seq 527과 동일하게 unchanged 상태입니다.
- 오늘(2026-04-20) docs-only round count는 0을 유지합니다. 이번 slice는 production Python + unit test code 변경입니다.
- broad dirty worktree는 그대로 남아 있고, 이번 slice에서 추가로 건드린 tracked file은 `pipeline_runtime/schema.py`와 `tests/test_pipeline_runtime_schema.py` 두 파일뿐입니다.
