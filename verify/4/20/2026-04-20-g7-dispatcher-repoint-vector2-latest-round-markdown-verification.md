# 2026-04-20 G7 dispatcher repoint vector2 latest_round_markdown verification

## 변경 파일
- `verify/4/20/2026-04-20-g7-dispatcher-repoint-vector2-latest-round-markdown-verification.md`

## 사용 skill
- `round-handoff`: seq 530 `.pipeline/claude_handoff.md`(Gemini 529 advice 기반 AXIS-V2) 구현 주장을 `pipeline_runtime/schema.py:273-297` 실제 HEAD 상태와 `tests/test_pipeline_runtime_schema.py:101-119` 실제 현재 상태에 대조하고, handoff가 요구한 narrowest 재검증(`py_compile`, `-k latest_round_markdown` subset, full module, watcher_core, supervisor 포커스 triple, operator_request_schema, pipeline_gui_backend, smoke 2 subset, `git diff --check`)을 직접 재실행해 truthful 여부를 확정했습니다.

## 변경 이유
- seq 527이 `latest_verify_note_for_work` singleton fallback 제거로 defect vector 1 (`VERIFY single-path lock-in`)을 닫은 뒤에도 seq 521에서 empirically validated 된 defect vector 2 (`4/18 WORK reverse-walk`, 17:12→17:04→16:58→16:42)가 `pipeline_runtime/schema.py:latest_round_markdown`의 `mtime` 단독 comparator에 그대로 남아 있었습니다.
- seq 530 handoff는 Gemini 529 advice대로 AXIS-V2 owner boundary fix를 선택해 `(date_key, mtime)` 튜플 비교로 chronological-first selection을 강제했습니다. 목표는 older-date note의 `mtime`가 더 커도 newer-date note가 선택되어 dispatcher가 더 이상 backwards walk를 하지 않도록 만드는 것이었습니다.

## 핵심 변경
- `pipeline_runtime/schema.py:273-297` `latest_round_markdown` 실제 상태
  - `:273` signature `def latest_round_markdown(directory: Path) -> tuple[str, float]:` 유지. 변경 없음.
  - `:274-276` locals: `best_path: Path | None = None`, `best_date = ""` (신규), `best_mtime = 0.0` 유지.
  - `:277-278` `if not directory.exists(): return "—", 0.0` 유지.
  - `:279-285` `rglob("*.md")` + `relative_to` guard + `len(rel.parts) < 3 or not ROUND_NOTE_NAME_RE.match(candidate.name)` guard 유지. ROUND_NOTE_NAME_RE `:32`는 `r"^\d{4}-\d{2}-\d{2}-.+\.md$"` 그대로.
  - `:286-289` mtime 취득 + `OSError` skip 유지.
  - `:290` `date_key = candidate.name[:10]` 신규 assignment.
  - `:291` comparator flip: `if (date_key, mtime) > (best_date, best_mtime):` (이전 `if mtime > best_mtime:` 에서 튜플 비교로 강화).
  - `:292-294` update: `best_path = candidate` + `best_date = date_key` (신규) + `best_mtime = mtime`.
  - `:295-297` 종료: `if best_path is None: return "—", 0.0` + `return str(best_path.relative_to(directory)), best_mtime` 유지. 반환 shape `tuple[str, float]` 불변.
- `pipeline_runtime/supervisor.py:36 import`, `:804 work call`, `:818 verify fallback call` 는 byte-for-byte 미변경 확인. consumer 계약 유지로 caller patch 불필요.
- `tests/test_pipeline_runtime_schema.py:82-99 test_latest_round_markdown_ignores_root_readme` 는 byte-for-byte 유지 확인.
- `tests/test_pipeline_runtime_schema.py:101-119` 신규 메서드 `test_latest_round_markdown_prefers_newer_date_over_newer_mtime`
  - 위치: `test_latest_round_markdown_ignores_root_readme` 직후, `class LoadJobStatesSharedFilesTest (:122)` 직전. handoff 지정 위치와 정합.
  - fixture: `root/4/18/2026-04-18-older-date.md`, `root/4/20/2026-04-20-newer-date.md` 두 파일 작성 후 older-date에 `spoofed_older_mtime = newer_mtime + 100.0` 를 `os.utime`로 적용.
  - 어서션: `rel == "4/20/2026-04-20-newer-date.md"` + `mtime == newer_mtime`. `spoofed_older_mtime`가 더 커도 `4/20` 파일이 선택됨을 확인.
- `LatestVerifyNoteForWorkTest` (7 메서드, `:337-525`)와 `PathEnforcedJobStateOwnershipTest` (7 메서드, `:170+`) 미변경 확인. seq 527 RESOLVE-B contract는 byte-for-byte 보존.
- 이번 라운드 편집 없는 파일 재확인: `watcher_core.py`, `pipeline_runtime/supervisor.py`, `verify_fsm.py`, `scripts/pipeline_runtime_gate.py`, `storage/sqlite_store.py`, `.pipeline/operator_request.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`, `tests/test_operator_request_schema.py`, `tests/test_pipeline_gui_backend.py`, `tests/test_watcher_core.py`, `tests/test_pipeline_runtime_supervisor.py`.
- `pipeline_runtime/schema.py:22-25 CONTROL_SLOT_LABELS` pre-existing dirty label-rename 유지.
- `.pipeline` rolling slot snapshot (검증 시각)
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `530` — shipped, 소비 완료.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `528` — seq 529 advice로 응답되어 stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `529` — seq 530으로 소비되어 stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `521` — canonical waiting_next_control / internal_only / next_slice_selection literals 그대로. vector 1+2 closure는 자연 전진이며 real operator-only blocker 없음.

## 검증
- 직접 코드/테스트 대조 (경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m py_compile pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py`
  - 결과: 출력 없음, 통과 (`PY_OK`).
- grep 실재 확인 (Read tool로 직접 `:273-297` body + `:101-119` 신규 test 확인, handoff가 기록한 counts는 honest):
  - `def latest_round_markdown` 1건 (`:273`).
  - `best_date` 3건 (`:275`, `:291`, `:293`).
  - `date_key` 3건 (`:290`, `:291`, `:293`) — /work honestly flagged handoff 기대치 2건과의 차이.
  - `best_mtime` 8건(schema.py 전체; `first_markdown` 공유 local 포함).
  - `ROUND_NOTE_NAME_RE` 3건(`:32`, `:284`, `:343`).
  - `def test_latest_round_markdown_` 2건(`:82`, `:101`).
  - `def test_` 36건.
  - `2026-04-18-older-date|2026-04-20-newer-date` 3건 — /work가 fixture 2건 + assertion 1건 차이를 honestly 기록.
  - `spoofed_older_mtime` 2건(`:112`, `:113`).
  - `candidate_count|latest_any` 0건 (seq 527 closure 보존).
- `python3 -m unittest -v tests.test_pipeline_runtime_schema -k latest_round_markdown`
  - 결과: `Ran 2 tests in 0.004s`, `OK`.
  - `test_latest_round_markdown_ignores_root_readme` PASS, `test_latest_round_markdown_prefers_newer_date_over_newer_mtime` PASS.
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - 결과: `Ran 36 tests in 0.054s`, `OK`. 35→36 net +1 정합. `LatestVerifyNoteForWorkTest` 7 green + `PathEnforcedJobStateOwnershipTest` 7 green 포함.
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 143 tests in 9.008s`, `OK`. caller 회귀 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_receipt_uses_verify_matching_job_work tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_marks_receipt_verify_missing_when_only_unrelated_verify_exists`
  - 결과: `Ran 3 tests in 0.028s`, `OK`. matching-verify 포커스 triple green.
- `python3 -m unittest tests.test_operator_request_schema tests.test_pipeline_gui_backend` (병합)
  - 결과: `Ran 52 / OK (skipped=0)` (6 + 46). 개별 baseline 정합.
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.016s`, `OK`.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.056s`, `OK`.
- `git diff --check -- pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py`
  - 결과: 출력 없음, 통과 (`DIFF_OK`).
- 실행하지 않은 항목 (명시):
  - `tests.test_web_app` 전체, Playwright isolated/suite, `make e2e-test`: 이번 변경은 selector 로직에만 영향을 주고 browser-visible 계약을 건드리지 않아 의도적 생략.
  - `tests.test_pipeline_runtime_supervisor` 전체 suite 재실행: handoff가 명시적으로 out-of-scope로 둔 3개 pre-existing baseline 실패(`test_build_artifacts_uses_canonical_round_notes_only`, `test_slot_verify_manifest_role_is_accepted_for_receipt`, `test_write_status_emits_receipt_and_control_block`)는 seq 527 시점과 동일한 상태일 것으로 기대됨. 이번 라운드에서는 matching-verify 포커스 triple 재실행으로 관련 축만 확인.

## 남은 리스크
- **defect vector 1+2 schema-layer 커버 완료, 런타임 관측 전**: seq 527 (vector 1) + seq 530 (vector 2) 로 schema.py의 두 selector가 모두 chronological/referenced 계약으로 강제됐지만, 실제 dispatcher가 이번 round 이후 다시 실행될 때까지는 backwards-walk 패턴이 실제로 사라졌는지 empirical 관측이 없습니다. 다음 dispatcher 가동 후 첫 `/verify`에서 VERIFY/WORK pair 추이를 다시 확인할 필요가 있습니다.
- **`date_key = candidate.name[:10]` 계약은 `ROUND_NOTE_NAME_RE`에 의존**: `pipeline_runtime/schema.py:32`의 `r"^\d{4}-\d{2}-\d{2}-.+\.md$"` 가 느슨해지면 앞 10글자가 `YYYY-MM-DD` 가 아닐 수 있어 비교가 조용히 깨집니다. 후속 regex 변경 시 guard 위치로 기억되어야 합니다.
- **이전 "max mtime only" semantics에 의존한 caller 미탐지의 한계**: 기존에 older note를 touch해서 일부러 재디스패치하는 흐름이 있었다면 이번 슬라이스는 그것을 숨기지 않고 test failure/blocked sentinel로 드러내는 방향을 유지했고, 현재 `tests.test_watcher_core` 143 green + supervisor matching-verify triple 3 green에서 그런 caller는 관측되지 않았습니다. runtime dispatch에 실제로 의존하는 코드 경로가 unit test로 커버되지 않는 구석에 남아 있을 가능성은 여전히 열려 있습니다.
- **supervisor 3-failure dirty baseline 미처리**: seq 527 당시와 동일한 3개 실패(`test_build_artifacts_uses_canonical_round_notes_only`, `test_slot_verify_manifest_role_is_accepted_for_receipt`, `test_write_status_emits_receipt_and_control_block`)는 handoff가 명시적으로 out-of-scope로 둔 상태이며 이번 라운드에서도 수정 범위가 아니었습니다. 축 자체가 다음 axis 후보로 여전히 남아 있습니다.
- **normalize_decision_class / normalize_reason_code pass-through**: 3 canonical literal runtime gating은 이번에도 강제되지 않았고 G7-gate-blocking / G11 / G8-pin / G3 / G9 / G10 / G6-sub2 / G6-sub3 는 계속 deferred.
- **unrelated `tests.test_web_app` 10 `LocalOnlyHTTPServer` PermissionError** 및 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state 관련 의심은 여전히 범위 밖.
- **docs round count**: 오늘(2026-04-20) docs-only round count는 0 유지. 이번 슬라이스는 production Python + unit test 계약 변경.
- **dirty worktree**: broad unrelated dirty 파일들(`controller/`, `pipeline_runtime/`, `pipeline_gui/`, `storage/`, `docs/`, 구버전 `/work`·`/verify` 등)과 `pipeline_runtime/schema.py:22-25` label-rename 차이는 그대로 남음. 이번 라운드 추가 stage 없음.
- **next slice ambiguity → Gemini-first**: vector 1+2 schema-layer closure 이후 남은 candidate(dispatcher runtime observability, supervisor 3 baseline failure triage, G7-gate-blocking, G11, G8-pin, G3, G9, G10, G6-sub2/sub3, test_web_app LocalOnlyHTTPServer 단일 cell, pipeline_gui_backend 45→46 doc-sync)는 서로 축이 다르고 single dominant current-risk reduction이 보이지 않습니다. today docs-only round count 0이고 real operator-only blocker 없음. 따라서 next control은 `.pipeline/operator_request.md` 보다 `.pipeline/gemini_request.md` (CONTROL_SEQ 531) 로 여는 편이 맞습니다.
