# 2026-04-20 G7 dispatcher repoint singleton removal RESOLVE-B

## 변경 파일
- `pipeline_runtime/schema.py`
- `tests/test_pipeline_runtime_schema.py`

## 사용 skill
- `onboard-lite`: implement lane 진입 전에 최신 `/work`, handoff, verify/operator 문맥, target 함수/테스트 소유 경계를 짧게 확인했습니다.
- `finalize-lite`: 실제 실행한 grep/unit test/diff 결과를 기준으로 release-check truth, doc-sync triage, `/work` closeout readiness를 함께 정리했습니다.

## 변경 이유
- seq 524 implement 시도는 `existing_test_fixture_depends_on_removed_fallback`로 막혔고, seq 525/526 Gemini arbitration이 RESOLVE-B를 확정했습니다.
- 이번 slice의 목적은 `latest_verify_note_for_work`가 same-day lone unreferenced verify note를 어떤 work에도 매칭해 버리던 singleton fallback을 제거해서 dispatcher-repoint의 `VERIFY single-path lock-in` defect vector를 닫는 것입니다.
- Gemini 526 결론대로, 기존 blocking fixture는 삭제가 아니라 negative-case contract로 보존하는 편이 맞아서 rename + `assertIsNone(resolved)` flip을 적용했습니다.

## 핵심 변경
- `pipeline_runtime/schema.py:360-408`의 `latest_verify_note_for_work`에서 singleton fallback 관련 추적을 제거했습니다.
  - 제거된 locals: `latest_any`, `latest_any_mtime`, `candidate_count`, `latest_any_refs`
  - 제거된 same-day loop bookkeeping: `candidate_count += 1`, `latest_any`/`latest_any_mtime`/`latest_any_refs` update block
  - 제거된 trailing fallback branch: `if candidate_count == 1 and not latest_any_refs: return latest_any`
  - 단순화된 반환 계약: explicit work reference가 있는 verify note만 반환하고, 그런 note가 없으면 `None`을 반환합니다.
- `tests/test_pipeline_runtime_schema.py`에서 RESOLVE-B에 맞춰 기존 2개 테스트 이름과 assertion을 뒤집었습니다.
  - `test_falls_back_to_single_same_day_verify_without_reference` → `test_returns_none_when_single_same_day_verify_has_no_reference`, assertion `self.assertEqual(resolved, verify_path)` → `self.assertIsNone(resolved)`
  - `test_cross_day_unrelated_verify_does_not_replace_same_day_fallback_rule` → `test_returns_none_when_same_day_unreferenced_and_cross_day_unrelated_both_present`, assertion `self.assertEqual(resolved, same_day_verify)` → `self.assertIsNone(resolved)`
  - 두 번째 renamed test는 method name에 `fallback` / `fallback_rule`를 남기지 않았고, fixture line `same_day_verify.write_text("# verify\n", encoding="utf-8")`와 cross-day unrelated verify write는 그대로 유지했습니다.
- 새 regression `test_returns_none_when_lone_unrelated_same_day_verify_mimics_manual_cleanup`를 `tests/test_pipeline_runtime_schema.py:497-524`에 추가했습니다.
  - fixture shape는 lone same-day verify file이 `2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md` 이름을 가지지만, 내용은 target work가 아니라 ``work/4/18/2026-04-18-other-slice.md`` 를 reference하는 경우입니다.
  - 기대 계약은 manual-cleanup처럼 보이는 파일명만으로는 매칭되지 않고 `None`을 반환해야 한다는 점입니다.
- `LatestVerifyNoteForWorkTest`의 나머지 4개 메서드
  - `test_prefers_explicit_work_reference_over_newer_unrelated_verify`
  - `test_accepts_cross_day_verify_when_note_explicitly_references_work`
  - `test_returns_none_when_multiple_same_day_verifies_do_not_reference_work`
  - `test_returns_none_when_single_same_day_verify_references_other_work`
  는 byte-for-byte 그대로 두었습니다.
- `PathEnforcedJobStateOwnershipTest`는 untouched 상태로 유지했습니다.
- 이번 round에서 편집하지 않은 파일:
  - `watcher_core.py`
  - `pipeline_runtime/supervisor.py`
  - `verify_fsm.py`
  - `.pipeline/operator_request.md`
  - `.pipeline/gemini_request.md`
  - `.pipeline/gemini_advice.md`
  - `tests/test_operator_request_schema.py`
  - `tests/test_pipeline_gui_backend.py`
  - `tests/test_watcher_core.py`
  - `tests/test_pipeline_runtime_supervisor.py`
- `pipeline_runtime/schema.py:22-25`의 pre-existing dirty label-rename diff는 그대로 두었고, revert도 extension도 하지 않았습니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474/477/480/483/486/489/495/498/501/504/507/510/513/516/517/518/519/520/521 shipped surfaces는 의도적으로 추가 수정하지 않았습니다.
- seq 524 implement_blocked (`HANDOFF_SHA 226bbcc643defd5e90103f39994f53740f57f6ba749826a7360586c917c6c4cb`)는 이번 seq 527 handoff의 RESOLVE-B 구현 상태로 닫혔습니다.
- doc-sync triage 결과 없음: 이번 변경은 dispatcher verify matching contract와 unit test만 바꿨고, README / product docs / browser contract 변경은 없었습니다.

## 검증
- grep 확인
  - `rg -n 'def latest_verify_note_for_work' pipeline_runtime/schema.py`
    - 결과: 1건 (`360:def latest_verify_note_for_work(`)
  - `rg -n 'candidate_count' pipeline_runtime/schema.py`
    - 결과: 0건
  - `rg -n 'latest_any' pipeline_runtime/schema.py`
    - 결과: 0건
  - `rg -n 'latest_referenced' pipeline_runtime/schema.py`
    - 결과: 10건
    - `latest_referenced_mtime` line도 같은 pattern에 같이 잡혀 handoff 기대치 4보다 많이 나왔습니다. 실제 hit는 `375`, `376`, `388`, `389`, `390`, `402`, `403`, `404`, `406`, `407`의 10 line입니다.
  - `rg -n 'def test_' tests/test_pipeline_runtime_schema.py`
    - 결과: 35건
    - 이 중 `LatestVerifyNoteForWorkTest`가 7개 메서드(`338`, `371`, `402`, `423`, `446`, `473`, `497`)를 차지합니다.
  - `rg -n 'test_returns_none_when_lone_unrelated_same_day_verify_mimics_manual_cleanup' tests/test_pipeline_runtime_schema.py`
    - 결과: 1건 (`497`)
  - `rg -n 'test_returns_none_when_single_same_day_verify_has_no_reference' tests/test_pipeline_runtime_schema.py`
    - 결과: 1건 (`402`)
  - `rg -n 'test_returns_none_when_same_day_unreferenced_and_cross_day_unrelated_both_present' tests/test_pipeline_runtime_schema.py`
    - 결과: 1건 (`446`)
  - `rg -n 'test_falls_back_to_single_same_day_verify_without_reference' tests/test_pipeline_runtime_schema.py`
    - 결과: 0건
  - `rg -n 'test_cross_day_unrelated_verify_does_not_replace_same_day_fallback_rule' tests/test_pipeline_runtime_schema.py`
    - 결과: 0건
  - `rg -n 'fallback' tests/test_pipeline_runtime_schema.py`
    - 결과: 18건
    - hit list: `178`, `187`, `190`, `209`, `211`, `228`, `276`, `293`, `298`, `317`, `548`, `569`, `570`, `589`, `607`, `645`, `711`, `723`
    - `LatestVerifyNoteForWorkTest` method name에는 0건이고, 모두 root fallback 관련 기존 test/comment 또는 process fingerprint fallback comment입니다.
  - `rg -n 'assertIsNone\(resolved\)' tests/test_pipeline_runtime_schema.py`
    - 결과: 5건 (`421`, `444`, `471`, `495`, `524`)
  - `rg -n 'manual-cleanup-keep-recent-zero-failsafe-verification' tests/test_pipeline_runtime_schema.py`
    - 결과: 1건 (`507`)
- `python3 -m py_compile pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py`
  - 결과: 출력 없음, 통과
- `python3 -m unittest tests.test_pipeline_runtime_schema.LatestVerifyNoteForWorkTest -v`
  - 결과: `Ran 7 tests in 0.040s`, `OK`
  - passing methods:
    - `test_prefers_explicit_work_reference_over_newer_unrelated_verify`
    - `test_accepts_cross_day_verify_when_note_explicitly_references_work`
    - `test_returns_none_when_single_same_day_verify_has_no_reference`
    - `test_returns_none_when_multiple_same_day_verifies_do_not_reference_work`
    - `test_returns_none_when_same_day_unreferenced_and_cross_day_unrelated_both_present`
    - `test_returns_none_when_single_same_day_verify_references_other_work`
    - `test_returns_none_when_lone_unrelated_same_day_verify_mimics_manual_cleanup`
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - 결과: `Ran 35 tests in 0.068s`, `OK`
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 143 tests in 7.568s`, `OK`
  - removed fallback에 caller가 직접 의존하는 red test는 나오지 않았습니다.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 93 tests in 0.689s`, `FAILED (failures=3)`
  - failing tests:
    - `test_build_artifacts_uses_canonical_round_notes_only`
    - `test_slot_verify_manifest_role_is_accepted_for_receipt`
    - `test_write_status_emits_receipt_and_control_block`
  - handoff 기대치의 "matching-verify 3 green; 6 pre-existing baseline failures unchanged"와는 현재 worktree baseline이 다릅니다.
  - 대신 matching-verify 관련 3개 타깃을 별도 재실행했습니다.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_receipt_uses_verify_matching_job_work tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_marks_receipt_verify_missing_when_only_unrelated_verify_exists`
  - 결과: `Ran 3 tests in 0.034s`, `OK`
- `python3 -m unittest -v tests.test_operator_request_schema`
  - 결과: `Ran 6 tests in 0.001s`, `OK`
- `python3 -m unittest -v tests.test_pipeline_gui_backend`
  - 결과: `Ran 46 tests in 0.133s`, `OK`
  - handoff 기대치 45와 달리 현재 worktree에서는 46개가 실행되었습니다.
- `python3 -m unittest -v tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.043s`, `OK`
- `python3 -m unittest -v tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.176s`, `OK`
- `git diff --check -- pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py`
  - 결과: 출력 없음, 통과
- 생략한 항목
  - `tests.test_web_app`, Playwright, `make e2e-test`는 handoff 범위와 무관한 browser/web 계약이라 실행하지 않았습니다.

## 남은 리스크
- 이번 변경은 `latest_verify_note_for_work` surface의 `VERIFY single-path lock-in` defect vector를 겨냥한 것이고, 두 번째 defect vector인 `4/18 WORK reverse-walk`는 같은 owner인지 아직 확정되지 않았습니다. dispatcher가 이후에도 backwards walk를 계속하면 별도 slice가 필요합니다.
- repo 어딘가의 dispatcher caller가 제거된 `candidate_count == 1` fallback에 실제로 의존했다면, 이번 slice는 그 의존을 call-site patch로 숨기지 않고 test failure/blocked sentinel로 드러내는 방향을 유지했습니다. 이번 round에서는 `tests.test_watcher_core`에서 그런 caller regression은 보이지 않았습니다.
- `normalize_decision_class` / `normalize_reason_code`는 여전히 pass-through이고, 3 canonical literal의 runtime gating은 이번 slice에서 강제하지 않았습니다.
- G7-gate-blocking, G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3는 모두 계속 deferred입니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 이번 라운드 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 0을 유지합니다. 이번 slice는 production Python + unit test code 기준의 변경입니다.
- broad dirty worktree는 그대로 남아 있고, 이번 slice 기준 변경 대상으로 취급한 것은 `pipeline_runtime/schema.py`와 `tests/test_pipeline_runtime_schema.py` 두 파일뿐입니다.
