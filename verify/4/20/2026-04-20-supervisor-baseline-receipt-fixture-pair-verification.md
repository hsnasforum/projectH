# 2026-04-20 supervisor baseline receipt fixture pair verification

## 변경 파일
- `verify/4/20/2026-04-20-supervisor-baseline-receipt-fixture-pair-verification.md`

## 사용 skill
- `round-handoff`: seq 539 `.pipeline/claude_handoff.md`(Gemini 538 AXIS-SUPERVISOR-BASELINE-2)가 주장한 `tests/test_pipeline_runtime_supervisor.py` 두 fixture truth-sync를 실제 HEAD 상태에 대조하고, handoff가 요구한 narrowest 재검증(`py_compile` 동등, 단일 메서드 2건 재실행, full supervisor suite 94 OK 확인, `git diff --check`)을 직접 재실행했습니다.

## 변경 이유
- seq 536이 1 baseline을 닫은 뒤에도 남아 있던 `test_write_status_emits_receipt_and_control_block` (`:292`)와 `test_slot_verify_manifest_role_is_accepted_for_receipt` (`:1069` post-edit) 실패는 두 테스트 모두 `artifact_path = "work/4/11/work-note.md"` 를 job-state JSON (`:341`, `:1112` post-edit) 에 쓰면서도 verify body를 bare `"# verify\n"` 로 두어 seq 527 referenced-match 계약을 만족하지 못한 결과였습니다.
- seq 539 handoff는 Gemini 538 advice대로 production 코드 변경 없이 두 verify fixture의 body 만 reference string 으로 교체해 receipt emission → `last_receipt_id` truthy → `runtime_state == "STOPPED"` → `degraded_reason == ""` 체인을 다시 end-to-end 로 활성화하는 것이 목적이었습니다.

## 핵심 변경
- `tests/test_pipeline_runtime_supervisor.py:353-356` 실제 상태
  - HEAD 에서 `verify_path.write_text(` / `"Based on \`work/4/11/work-note.md\`\n",` / `encoding="utf-8",` / `)` 4줄 multi-line 구성 확인. `:352` `verify_path = verify_dir / "2026-04-11-verify.md"` 는 미변경.
  - `test_write_status_emits_receipt_and_control_block` (method def `:292`) 의 다른 fixture/mock/assertion 라인(`:293-351, :358-385`)은 byte-for-byte 유지 확인.
- `tests/test_pipeline_runtime_supervisor.py:1123-1126` 실제 상태
  - HEAD 에서 `(verify_dir / "2026-04-11-verify.md").write_text(` / `"Based on \`work/4/11/work-note.md\`\n",` / `encoding="utf-8",` / `)` 4줄 multi-line 구성 확인.
  - `test_slot_verify_manifest_role_is_accepted_for_receipt` (method def post-edit `:1069`) 의 다른 setup/assertion 라인(`:1070-1122, :1128-1131`)은 byte-for-byte 유지 확인.
- reference string `"Based on \`work/4/11/work-note.md\`\n"` 은 `note_referenced_work_paths` 파서가 인식하는 형태이고, 두 테스트 모두 `artifact_path` 값 `"work/4/11/work-note.md"` 와 바이트-정합.
- seq 536 fixture (`:203-206 test_build_artifacts_uses_canonical_round_notes_only`) byte-for-byte 유지. seq 533 sibling test (`:250-290 test_build_artifacts_emits_dispatch_selection_event`) 미변경.
- 이번 라운드 편집 없는 파일 재확인: `pipeline_runtime/schema.py`, `pipeline_runtime/supervisor.py`, `watcher_core.py`, `verify_fsm.py`, `scripts/pipeline_runtime_gate.py`, `storage/sqlite_store.py`, `.pipeline/operator_request.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`, `tests/test_pipeline_runtime_schema.py`, `tests/test_watcher_core.py`, `tests/test_operator_request_schema.py`, `tests/test_pipeline_gui_backend.py`, `tests/test_smoke.py`.
- seq 527/530/533/536 계약 byte-for-byte 보존.
- `.pipeline` rolling slot snapshot (검증 시각)
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `539` — shipped, 소비 완료.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `537` — advice 538로 응답되어 stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `538` — seq 539로 소비되어 stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `521` — canonical literals 보존.

## 검증
- 직접 코드 Read 대조 완료 (경로·라인은 ## 핵심 변경 참조).
- grep 교차 확인 (handoff hit counts 와 정합):
  - `def test_write_status_emits_receipt_and_control_block` `tests/test_pipeline_runtime_supervisor.py` 1건 (`:292`).
  - `def test_slot_verify_manifest_role_is_accepted_for_receipt` `tests/test_pipeline_runtime_supervisor.py` 1건 (`:1069` post-edit; seq 539 handoff의 pre-edit `:1063` 대비 multi-line 교체로 인한 6-line shift, 내용 일치).
  - `Based on .work/4/11/work-note.md.` 2건 (`:354`, `:1124`).
  - `Based on .work/4/16/2026-04-16-real-round.md.` 1건 (`:204`, seq 536 fixture 보존).
  - bare `"# verify\n"` 잔존 hit 1건(`:1057`) — handoff 가 의도적으로 out-of-scope 로 둔 manifest-mismatch 계열 fixture 로 확인.
  - `def test_` 94건 (이번 라운드 테스트 추가/삭제 없음).
  - `dispatch_selection` `pipeline_runtime/supervisor.py` 1건 (`:820`) — seq 533 emit 보존.
  - `candidate_count|latest_any` `pipeline_runtime/schema.py` 0건 (seq 527 closure 보존).
  - `date_key` `pipeline_runtime/schema.py` 3건 — seq 530 계약 보존.
- `python3 -m py_compile tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, 통과 (handoff 재현 + 본 verify 직접 확인 정합).
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_emits_receipt_and_control_block tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_slot_verify_manifest_role_is_accepted_for_receipt`
  - 결과: `Ran 2 tests in 0.045s`, `OK`. 두 previously-red 가 모두 green 으로 전환.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor -k build_artifacts`
  - handoff 기록: `Ran 3 / OK`. 본 verify round 직접 재실행 생략 (아래 full-suite 가 이 3건을 포함해 OK 로 증명).
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 94 tests in 0.627s`, `OK`. 3-baseline chain 완전히 닫힘. 이전에 green 이던 다른 어떤 테스트도 red 로 뒤집히지 않음.
- matching-verify focused triple + 병합 regression 은 handoff 기록 인용 (`tests.test_pipeline_runtime_schema` 36 OK, `tests.test_watcher_core` 143 OK, `tests.test_operator_request_schema` 6 OK, `tests.test_pipeline_gui_backend` 46 OK, smoke 11/27 OK). 이번 변경이 unit-test fixture 두 블록에만 국한되어 다른 모듈 계약에 영향을 줄 수 있는 경로가 없음이 명백하므로 verify round 에서 full 재실행은 생략.
- `git diff --check -- tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, 통과 (`DIFF_OK`).
- 실행하지 않은 항목 (명시):
  - `tests.test_web_app`, Playwright, `make e2e-test`: 이번 변경은 unit-test fixture 수정이며 browser-visible 계약 밖. 의도적 생략.
  - `:1057` bare `"# verify\n"` 나 기타 `latest_verify_note_for_work` consumer fixture 전수 audit: Gemini 538 이 pin 하지 않았고 handoff 가 scope 외로 명시. AXIS-STALE-REFERENCE-AUDIT 은 후속 축 후보로 남김.

## 남은 리스크
- **supervisor baseline 3-chain closed**: 오늘 라운드 시작 시의 3 pre-existing failure 는 seq 536 (1건) + seq 539 (2건) 조합으로 모두 닫혔습니다. 그러나 이번 truth-sync 는 test-fixture layer 에서만 진행됐고, production-side regression 가능성이 있던 2번째·3번째 failure 역시 실제로는 seq 527 contract cascade 였음이 확인됐습니다. production behavior 변화는 없었음을 재강조.
- **남아 있는 bare `"# verify\n"` 1건**: `tests/test_pipeline_runtime_supervisor.py:1057` 주변 manifest-mismatch 계열 fixture 는 handoff 가 명시적으로 out-of-scope 로 뒀습니다. 이 테스트는 현재 green 이지만 상위 계약 변경이 있을 때 재발 가능성이 남습니다. AXIS-STALE-REFERENCE-AUDIT 축이 이 구역 포함해서 audit 할 후보입니다.
- **AXIS-OBSERVE-EVALUATE 미실행**: seq 533 `dispatch_selection` emit 의 monotonic-nondecreasing 순서를 경험적으로 검증하는 test slice 는 여전히 오픈. 현 supervisor suite green 상태에서 자연스럽게 다음 라운드 후보.
- **schema-layer contract 보존**: seq 527 `latest_verify_note_for_work`, seq 530 `latest_round_markdown`, seq 533 `_build_artifacts` `dispatch_selection`, seq 536 canonical-round-notes fixture 모두 byte-for-byte 유지.
- **G7-gate-blocking, G11, G8-pin, G3, G9, G10, G6-sub2/sub3** 전부 deferred, `tests.test_web_app` 10 `LocalOnlyHTTPServer` PermissionError 그대로, `pipeline_gui_backend` 46 baseline.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 유지. 이번 슬라이스는 unit-test fixture 수정.
- **dirty worktree**: broad unrelated dirty 파일들과 `pipeline_runtime/schema.py:22-25` 유지.
- **next slice ambiguity → Gemini-first**: 남은 candidate(AXIS-STALE-REFERENCE-AUDIT — `:1057` 포함 범위 / AXIS-OBSERVE-EVALUATE / G4 / G7-GATE / G5-DEGRADED / G6-TEST-WEB-APP / G11 / G8-PIN / DOCS-BUNDLE)은 축이 서로 다르고 single dominant current-risk reduction 이 명확하지 않습니다. 오늘 docs-only round count 0, real operator-only blocker 없음. 따라서 next control 은 `.pipeline/operator_request.md` 보다 `.pipeline/gemini_request.md` (CONTROL_SEQ 540) 로 여는 편이 맞습니다.
