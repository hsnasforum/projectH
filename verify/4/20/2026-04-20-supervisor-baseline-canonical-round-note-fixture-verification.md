# 2026-04-20 supervisor baseline canonical round note fixture verification

## 변경 파일
- `verify/4/20/2026-04-20-supervisor-baseline-canonical-round-note-fixture-verification.md`

## 사용 skill
- `round-handoff`: seq 536 `.pipeline/claude_handoff.md`(Gemini 535 AXIS-SUPERVISOR-BASELINE을 seq 534 "triage ONE" 프레임으로 narrow 한 primary fix)가 주장한 `tests/test_pipeline_runtime_supervisor.py:203-206` fixture truth-sync를 실제 HEAD 상태에 대조하고, handoff가 요구한 narrowest 재검증(`py_compile`, 단일 메서드 재실행, `-k build_artifacts` 3 subset, full supervisor suite failures=2 확인, `git diff --check`)을 직접 재실행했습니다.

## 변경 이유
- seq 527 `latest_verify_note_for_work`가 referenced-match only → `None` 으로 계약을 바꾼 뒤 `test_build_artifacts_uses_canonical_round_notes_only` 의 기존 fixture `verify_note.write_text("# verify\n", ...)`는 어떤 work도 참조하지 못해 `verify_rel = "—"` 를 반환받고 baseline failure를 구성하고 있었습니다.
- seq 536 handoff는 production 수정 없이 한 줄 fixture 교체로 이 stale assertion을 닫는 것이었고, 다른 2 baseline 실패(`test_slot_verify_manifest_role_is_accepted_for_receipt`, `test_write_status_emits_receipt_and_control_block`)는 Gemini 535가 root cause 를 pin 하지 않아 범위 외로 deferred 됐습니다.

## 핵심 변경
- `tests/test_pipeline_runtime_supervisor.py:203-206` 실제 상태
  - HEAD 에서 한 줄 `verify_note.write_text("# verify\n", encoding="utf-8")` 가 handoff 지정 multi-line 형태로 교체되어 있음을 Read 로 확인.
  - `:203` `verify_note.write_text(` , `:204` `"Based on \`work/4/16/2026-04-16-real-round.md\`\n",` , `:205` `encoding="utf-8",` , `:206` `)` 4 줄 구성. leading indent 12 spaces 유지.
  - `:190-217` 의 나머지 부분(`_write_active_profile`, `work_readme`/`verify_readme`/`work_note`/`verify_note` Path 구성, `parent.mkdir`, `work_note.write_text("# work\n", ...)`, `work_readme.write_text("# metadata\n", ...)`, `verify_readme.write_text("# metadata\n", ...)`, `os.utime` 4 행 100/200/300/400, `RuntimeSupervisor(root, start_runtime=False)`, `supervisor._build_artifacts()`, 두 `assertEqual` 라인)는 byte-for-byte 유지 확인. test 의 원래 의도(canonical round note 가 README 보다 우선) 그대로.
  - reference string 은 sibling 테스트 `test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify` (`:219-248`) 가 쓰는 `"Based on \`work/<...>.md\`\n"` 패턴과 동일. `note_referenced_work_paths` 파서가 인식하는 형태.
- 이번 라운드 편집 없는 파일 재확인: `pipeline_runtime/schema.py`, `pipeline_runtime/supervisor.py`, `watcher_core.py`, `verify_fsm.py`, `scripts/pipeline_runtime_gate.py`, `storage/sqlite_store.py`, `.pipeline/operator_request.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`, `tests/test_pipeline_runtime_schema.py`, `tests/test_watcher_core.py`, `tests/test_operator_request_schema.py`, `tests/test_pipeline_gui_backend.py`, `tests/test_smoke.py`.
- `pipeline_runtime/schema.py:22-25 CONTROL_SLOT_LABELS` pre-existing dirty label-rename 유지. seq 527 `latest_verify_note_for_work` / seq 530 `latest_round_markdown` / seq 533 `_build_artifacts` `dispatch_selection` 계약 byte-for-byte 보존.
- `.pipeline` rolling slot snapshot (검증 시각)
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `536` — shipped, 소비 완료.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `534` — advice 535로 응답되어 stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `535` — seq 536으로 소비되어 stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `521` — canonical waiting_next_control / internal_only / next_slice_selection literals 보존.

## 검증
- 직접 코드 Read 대조 완료 (경로·라인은 ## 핵심 변경 참조).
- grep 교차 확인(handoff 의 hit counts 와 정합):
  - `def test_build_artifacts_uses_canonical_round_notes_only` 1건 (`:190`).
  - `Based on .work/4/16/2026-04-16-real-round.md.` 1건 (`:204`).
  - `verify_note.write_text` 2건 (`:203` 타깃 메서드 + `:262` sibling emit event test).
  - `def test_slot_verify_manifest_role_is_accepted_for_receipt` 1건 (`:1063`) 미변경.
  - `def test_write_status_emits_receipt_and_control_block` 1건 (`:292`) 미변경.
  - `def test_` 94건 — 이번 라운드 테스트 추가/삭제 없음.
  - `dispatch_selection` `pipeline_runtime/supervisor.py` 1건 (`:820`) — seq 533 emit 보존.
  - `candidate_count|latest_any` `pipeline_runtime/schema.py` 0건 — seq 527 closure 보존.
  - `date_key` `pipeline_runtime/schema.py` 3건 — seq 530 계약 보존.
- `python3 -m py_compile tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, 통과 (handoff 재현 및 본 verify 직접 실행 정합).
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_uses_canonical_round_notes_only`
  - handoff 기록: `Ran 1 / OK`. 본 verify 직접 재실행 확인: baseline 실패에서 green 으로 전환.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor -k build_artifacts`
  - 결과: `Ran 3 tests in 0.023s`, `OK`. `test_build_artifacts_uses_canonical_round_notes_only` 포함 3건 모두 PASS.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 94 tests in 0.693s`, `FAILED (failures=2)`.
  - 남은 실패는 정확히 handoff 기대치의 두 이름:
    - `test_slot_verify_manifest_role_is_accepted_for_receipt` (`'DEGRADED' != 'STOPPED'`)
    - `test_write_status_emits_receipt_and_control_block` (`'' is not true`)
  - 이전 baseline 3건 → 2건으로 정확히 1건 감소, `test_build_artifacts_uses_canonical_round_notes_only` 가 new green 으로 전환. 다른 어떤 테스트도 red 로 뒤집히지 않음.
- matching-verify focused triple + 병합 regression 는 handoff 기록 기준으로 사용: `tests.test_pipeline_runtime_schema` 36 OK, `tests.test_watcher_core` 143 OK, `tests.test_operator_request_schema` 6 OK, `tests.test_pipeline_gui_backend` 46 OK, `tests.test_smoke -k progress_summary` 11 OK, `-k coverage` 27 OK. 이번 변경이 unit-test fixture 1 블록에만 국한되어 다른 모듈 계약에 영향을 줄 수 있는 경로가 없음이 명백하므로 본 verify round 에서 full 재실행은 생략.
- `git diff --check -- tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, 통과 (`DIFF_OK`).
- 실행하지 않은 항목 (명시):
  - `tests.test_web_app`, Playwright, `make e2e-test`: 이번 변경은 unit-test fixture 변경이며 browser-visible 계약 밖. 의도적 생략.
  - 나머지 2 baseline failure 의 root-cause triage: Gemini 535가 root cause를 pin 하지 않았고 handoff scope 밖. 이번 round 에서 수정하지 않음.

## 남은 리스크
- **supervisor baseline 2건 잔존**: `test_slot_verify_manifest_role_is_accepted_for_receipt` (`DEGRADED != STOPPED`)와 `test_write_status_emits_receipt_and_control_block` (`'' is not true`)는 failure mode 가 seq 527 stale-assertion 과 다르고 production-side regression 혹은 환경 의존일 가능성이 있어 별도 Gemini arbitration 이 필요합니다.
- **stale-reference fixture 잔존 가능성**: 이번 수정은 단일 fixture truth-sync. 다른 test-side consumer 가 `latest_verify_note_for_work` 의 `assertEqual(resolved, <path>)` 패턴을 reference 없이 쓰는 경우가 더 있는지 전수 audit 은 하지 않았습니다.
- **seq 527/530/533 계약 보존 확인**: schema / supervisor 쪽은 이번 라운드에서 byte-for-byte 유지됨.
- **empirical dispatcher probe 미관측**: seq 533 `dispatch_selection` emit 이 실제 runtime dispatch 라운드에서 기록한 date 단조성은 여전히 별도 evaluation slice(AXIS-OBSERVE-EVALUATE 후보)가 필요합니다.
- **G7-gate-blocking, G11, G8-pin, G3, G9, G10, G6-sub2/sub3** 전부 deferred, `tests.test_web_app` 10 `LocalOnlyHTTPServer` PermissionError 그대로, `pipeline_gui_backend` 46 건이 baseline.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 유지. 이번 슬라이스는 unit-test fixture 수정.
- **dirty worktree**: broad unrelated dirty 파일들과 `pipeline_runtime/schema.py:22-25` 유지. 이번 라운드 추가 stage 없음.
- **next slice ambiguity → Gemini-first**: 남은 candidate(남은 2 supervisor baseline 각각 / AXIS-OBSERVE-EVALUATE / stale-reference fixture 전수 audit / G4 / G7-GATE / G5-DEGRADED / G6-TEST-WEB-APP / G11 / G8-PIN / DOCS-BUNDLE)은 축이 서로 다르고 single dominant current-risk reduction 이 보이지 않습니다. 오늘 docs-only round count 0, real operator-only blocker 없음. 따라서 next control 은 `.pipeline/operator_request.md` 보다 `.pipeline/gemini_request.md` (CONTROL_SEQ 537) 로 여는 편이 맞습니다.
