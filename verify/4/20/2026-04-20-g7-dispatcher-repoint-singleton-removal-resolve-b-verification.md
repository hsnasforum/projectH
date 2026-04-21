# 2026-04-20 G7 dispatcher repoint singleton removal RESOLVE-B verification

## 변경 파일
- `verify/4/20/2026-04-20-g7-dispatcher-repoint-singleton-removal-resolve-b-verification.md`

## 사용 skill
- `round-handoff`: seq 527 `.pipeline/claude_handoff.md`(Gemini 526 advice 기반 RESOLVE-B) 구현 주장을 `pipeline_runtime/schema.py` 실제 HEAD 상태와 `tests/test_pipeline_runtime_schema.py` 실제 현재 상태에 대조하고, handoff가 요구한 narrowest 재검증(`py_compile`, `LatestVerifyNoteForWorkTest -v`, full module, watcher_core, supervisor 포커스 triple, operator_request_schema, pipeline_gui_backend, smoke -k progress_summary/coverage, `git diff --check`)을 직접 재실행해 truthful 여부를 확정했습니다.

## 변경 이유
- seq 527 `.pipeline/claude_handoff.md`(STATUS `implement`, CONTROL_SEQ 527, HANDOFF_SHA 226bbcc...에 묶인 seq 524 sentinel을 RESOLVE-B로 전환)가 실행되어 새 `/work` 노트 `work/4/20/2026-04-20-g7-dispatcher-repoint-singleton-removal-resolve-b.md`가 제출되었습니다.
- 목표는 `latest_verify_note_for_work` 내부의 `candidate_count == 1 and not latest_any_refs` singleton fallback 분기를 제거해 `VERIFY single-path lock-in` defect vector를 닫고, 기존 blocking test 2개를 rename + assertion flip(`assertIsNone`)으로 negative-case 계약으로 보존하며, 새 regression `test_returns_none_when_lone_unrelated_same_day_verify_mimics_manual_cleanup` 1건을 추가하는 것이었습니다.
- 두 번째 defect vector(`4/18 WORK reverse-walk`), 그리고 G7-gate-blocking / G11 / G8-pin / G3 / G9 / G10 / G6-sub2/sub3는 의도적으로 범위 외였습니다.

## 핵심 변경
- `pipeline_runtime/schema.py:360-408` `latest_verify_note_for_work` 실제 상태
  - `:360-371` signature + `normalize_repo_artifact_path` guard + `verify_root.exists()` early return 그대로 유지.
  - `:373` `verify_dir = same_day_verify_dir_for_work(...)` 유지.
  - `:375-376` 새 locals: `latest_referenced: Path | None = None`, `latest_referenced_mtime = 0.0`. `latest_any`, `latest_any_mtime`, `candidate_count`, `latest_any_refs` 초기화는 현재 파일에 0건.
  - `:377-390` same-day loop: `is_canonical_round_note` 가드 + `mtime` 취득 + `note_referenced_work_paths` 계산 후 `normalized_work not in refs` 면 `continue`. 참조 매치일 때만 `latest_referenced` / `latest_referenced_mtime` 갱신. `candidate_count += 1`/`latest_any*` 업데이트 블록은 제거됨.
  - `:392-404` cross-day referenced loop: `verify_root.rglob("*.md")`를 돌며 canonical round note + reference match 조건이면 `latest_referenced`를 갱신. 이 루프는 seq 527이 "do NOT touch" 범위로 명시했고 확인 결과 byte-for-byte 유지.
  - `:406-408` return branch: `if latest_referenced is not None: return latest_referenced` + `return None`. 기존 `if candidate_count == 1 and not latest_any_refs: return latest_any` 분기는 존재하지 않음.
  - HEAD 계약: 명시적으로 work를 참조하는 verify note만 반환, 없으면 `None`. `lone unreferenced same-day verify`를 만능 매치로 돌려주는 동작은 제거됨.
- `tests/test_pipeline_runtime_schema.py:337-525` `LatestVerifyNoteForWorkTest` 실제 상태
  - `:338` `test_prefers_explicit_work_reference_over_newer_unrelated_verify`: 미변경 확인.
  - `:371` `test_accepts_cross_day_verify_when_note_explicitly_references_work`: 미변경 확인.
  - `:402` `test_returns_none_when_single_same_day_verify_has_no_reference`: 구 이름 `test_falls_back_to_single_same_day_verify_without_reference` → 현 이름으로 rename, `:421` 에서 `self.assertIsNone(resolved)` 로 flip.
  - `:423` `test_returns_none_when_multiple_same_day_verifies_do_not_reference_work`: 미변경 확인, `:444` `assertIsNone`.
  - `:446` `test_returns_none_when_same_day_unreferenced_and_cross_day_unrelated_both_present`: 구 이름 `test_cross_day_unrelated_verify_does_not_replace_same_day_fallback_rule` → 현 이름으로 rename, `:471` 에서 `self.assertIsNone(resolved)` 로 flip. 메서드 이름에 `fallback`/`fallback_rule` 없음(검증됨).
  - `:473` `test_returns_none_when_single_same_day_verify_references_other_work`: 미변경, `:495` `assertIsNone`.
  - `:497-524` 신규 `test_returns_none_when_lone_unrelated_same_day_verify_mimics_manual_cleanup`: fixture에서 `verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`가 실존하지만 내용은 `work/4/18/2026-04-18-other-slice.md` 를 참조하고, target은 `work/4/18/2026-04-18-slice.md`. 어서션은 `self.assertIsNone(resolved)` 로 manual-cleanup처럼 보이는 파일명만으로는 매칭되지 않음을 명시.
- `PathEnforcedJobStateOwnershipTest` (`:170` 이하 7개 메서드)는 미변경 확인.
- 이번 라운드에서 편집되지 않은 파일들(seq 527 handoff 명시): `watcher_core.py`, `pipeline_runtime/supervisor.py`, `verify_fsm.py`, `pipeline-launcher.py`, `.pipeline/operator_request.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`, `tests/test_operator_request_schema.py`, `tests/test_pipeline_gui_backend.py`, `tests/test_watcher_core.py`, `tests/test_pipeline_runtime_supervisor.py`. 모두 HEAD에서 변경 없음을 `git diff --check` + narrow grep 확인.
- `pipeline_runtime/schema.py:22-25` pre-existing dirty label-rename 차이는 여전히 dirty 로 남아 있고 이번 라운드는 건드리지 않음.
- `.pipeline` rolling slot snapshot (검증 시각 기준)
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `527` — shipped, 소비 완료.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `525` — advice 526로 응답되어 stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `526` — seq 527로 소비되어 stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `521` — canonical `waiting_next_control` / `internal_only` / `next_slice_selection` literals 그대로 유지. FIX_DISPATCHER_REPOINT vector 1 closure는 자연 전진 취급이며 real operator-only blocker는 없음.

## 검증
- 직접 코드/테스트 대조 (경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m py_compile pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py`
  - 결과: 출력 없음, 통과 (`PY_COMPILE_OK`).
- `rg -n 'def latest_verify_note_for_work' pipeline_runtime/schema.py`
  - 결과: 1건 (`360:def latest_verify_note_for_work(`).
- `rg -n 'candidate_count' pipeline_runtime/schema.py`
  - 결과: 0건.
- `rg -n 'latest_any' pipeline_runtime/schema.py`
  - 결과: 0건.
- `rg -n 'latest_referenced' pipeline_runtime/schema.py`
  - 결과: 10건 (`375`, `376`, `388`, `389`, `390`, `402`, `403`, `404`, `406`, `407`). `latest_referenced_mtime` 4개 라인이 같은 pattern에 잡혀 handoff 기대 "4 hits"보다 많지만 구조상 동일.
- `rg -n '(def test_|class LatestVerifyNoteForWorkTest)' tests/test_pipeline_runtime_schema.py`
  - `LatestVerifyNoteForWorkTest` (`:337`) 클래스가 7개 메서드(`:338`, `:371`, `:402`, `:423`, `:446`, `:473`, `:497`) 보유. handoff 기대치(6 → 7 net +1) 정합.
- `rg -n 'test_returns_none_when_lone_unrelated_same_day_verify_mimics_manual_cleanup|test_returns_none_when_single_same_day_verify_has_no_reference|test_returns_none_when_same_day_unreferenced_and_cross_day_unrelated_both_present' tests/test_pipeline_runtime_schema.py`
  - 결과: 각각 `:497`, `:402`, `:446`에 1건씩.
- `rg -n 'test_falls_back_to_single_same_day_verify_without_reference|test_cross_day_unrelated_verify_does_not_replace_same_day_fallback_rule' tests/test_pipeline_runtime_schema.py`
  - 결과: 0건 (구 이름 완전 제거).
- `rg -n 'assertIsNone\(resolved\)' tests/test_pipeline_runtime_schema.py`
  - 결과: 5건 (`:421`, `:444`, `:471`, `:495`, `:524`).
- `rg -n 'manual-cleanup-keep-recent-zero-failsafe-verification' tests/test_pipeline_runtime_schema.py`
  - 결과: 1건 (`:507`).
- `python3 -m unittest tests.test_pipeline_runtime_schema.LatestVerifyNoteForWorkTest -v`
  - 결과: `Ran 7 tests in 0.042s`, `OK`. 7개 메서드 전부 pass.
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - 결과: `Ran 35 tests in 0.075s`, `OK` (`PathEnforcedJobStateOwnershipTest` 7 + `LatestVerifyNoteForWorkTest` 7 + 21 기타).
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 143 tests in 8.857s`, `OK`. 제거된 singleton fallback에 caller가 의존한 regression 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_receipt_uses_verify_matching_job_work tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_marks_receipt_verify_missing_when_only_unrelated_verify_exists`
  - 결과: `Ran 3 tests in 0.058s`, `OK`. matching-verify 포커스 triple green.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor` (전체)
  - 결과: `Ran 93 tests in 0.916s`, `FAILED (failures=3)`. 실패 항목: `test_build_artifacts_uses_canonical_round_notes_only`, `test_slot_verify_manifest_role_is_accepted_for_receipt`, `test_write_status_emits_receipt_and_control_block`. seq 527 handoff의 "6 pre-existing baseline failures unchanged" 기대치와는 다른 현재 dirty-worktree baseline이지만, seq 527 `/work`가 이 차이를 그대로 기록했고 matching-verify 세 가지는 포커스 rerun으로 green 입증.
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과 (병합 수): 전체 52건(pipeline_gui_backend 46 + operator_request_schema 6) `OK`. 개별 재현: `Ran 6 / OK (skipped=0)` (operator_request_schema), `Ran 46 / OK (skipped=0)` (pipeline_gui_backend). handoff 기대(45)보다 1개 많은 것은 seq 527 `/work`가 해당 deviation을 이미 honestly 기록함.
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.024s`, `OK`.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.068s`, `OK`.
- `git diff --check -- pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py`
  - 결과: 출력 없음, 통과 (`DIFF_CHECK_OK`).
- 실행하지 않은 항목 (명시):
  - `tests.test_web_app` 전체, Playwright isolated/suite, `make e2e-test`: 이번 변경은 verify-dispatch 계약에만 영향이며 browser-visible 계약을 건드리지 않았으므로 의도적으로 생략.
  - supervisor 6 pre-existing baseline failures 수정 시도: 범위 외, 포커스 rerun으로만 matching-verify 축 확인.
  - `tests.test_watcher_core`의 fail-on-red sentinel 전환 검사: 143건 전부 green이므로 추가 triage 불필요.

## 남은 리스크
- **defect vector 2 미해결**: `VERIFY single-path lock-in` (vector 1) 은 이번 슬라이스로 `latest_verify_note_for_work` surface에서 닫혔지만, `4/18 WORK reverse-walk` (vector 2) 는 여전히 열려 있습니다. seq 521 operator_request가 두 vector 모두의 dispatcher owner 지정을 요구했으나 실제 구현 dispatch는 vector 1만 잡았습니다. 후속 라운드에서 dispatcher가 다시 backwards walk를 하면 vector 2 전용 slice가 필요하며, 이번 round에서는 런타임 dispatch가 일어나지 않았기에 실제 회귀 여부는 관찰되지 않았습니다.
- **`candidate_count == 1` fallback에 의존한 caller 미탐지의 한계**: `tests.test_watcher_core` 143건 + `tests.test_pipeline_runtime_supervisor` matching-verify 3건은 green이지만, runtime dispatch 경로 중 unit test로 커버되지 않는 corner가 있다면 `latest_verify_note_for_work` → `None` 반환이 downstream에서 `receipt_verify_missing` 계열로 드러날 수 있습니다. 이번 라운드 fail-on-red sentinel은 발동되지 않았고 caller 쪽 silent patch는 의도적으로 회피했습니다.
- **supervisor 3-failure dirty baseline**: `test_build_artifacts_uses_canonical_round_notes_only`, `test_slot_verify_manifest_role_is_accepted_for_receipt`, `test_write_status_emits_receipt_and_control_block`은 이번 변경과 무관한 pre-existing 실패로 그대로 남아 있습니다. seq 527 `/work`가 handoff 기대치와 baseline 차이를 honestly 기록했고, 이번 라운드는 수정 범위가 아닙니다.
- **pipeline_gui_backend test count drift**: 현재 46 건(handoff 기대 45). deviation은 harmless 하지만 다음 doc-sync 기회에 handoff 기대치의 출처(과거 45 baseline)를 재확인하는 편이 깔끔합니다.
- **dispatcher-repoint defect vector 2 owner ambiguity**: vector 1 해결로 `candidate_count == 1` 만능 fallback은 사라졌지만, 같은 `latest_verify_note_for_work`가 vector 2 backwards walk 패턴을 추가 유발할 소유자인지 아직 미확정. 후속 Gemini 중재 입력이 필요합니다.
- **normalize_decision_class / normalize_reason_code pass-through**: 3 canonical literal의 런타임 gating은 여전히 강제되지 않았고, G7-gate-blocking / G11 / G8-pin / G3 / G9 / G10 / G6-sub2 / G6-sub3 는 계속 deferred.
- **unrelated `tests.test_web_app` `LocalOnlyHTTPServer` PermissionError 10건** 및 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state 관련 불안정은 여전히 이번 라운드 범위 밖.
- **docs round count**: 오늘(2026-04-20) docs-only round count는 0 유지. 이번 슬라이스는 production Python + unit test 계약 변경이며 doc-sync drift는 신규로 만들지 않았습니다.
- **dirty worktree**: broad unrelated dirty 파일들(`controller/`, `pipeline_runtime/`, `pipeline_gui/`, `storage/`, `docs/`, `/work`·`/verify` 구버전 등)과 `pipeline_runtime/schema.py:22-25` 의 pre-existing label-rename 차이는 그대로 남아 있습니다. 이번 라운드는 2 대상 파일 외에 추가 stage가 없습니다.
- **next slice ambiguity → Gemini-first**: vector 2(dispatcher backwards-walk follow-up), G7-gate-blocking, G11, G8-pin, G3, G9, G10, G6-sub2/sub3 사이에 single obvious dominant current-risk reduction이 보이지 않습니다. 오늘 docs-only round count가 0이고 real operator-only blocker가 없으므로 `/verify` README 규칙대로 next control은 `.pipeline/operator_request.md` 보다 `.pipeline/gemini_request.md`(CONTROL_SEQ 528) 로 축 선정 arbitration을 여는 편이 맞습니다.
