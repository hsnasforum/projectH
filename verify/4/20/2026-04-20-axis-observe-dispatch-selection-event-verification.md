# 2026-04-20 AXIS-OBSERVE dispatch_selection event verification

## 변경 파일
- `verify/4/20/2026-04-20-axis-observe-dispatch-selection-event-verification.md`

## 사용 skill
- `round-handoff`: seq 533 `.pipeline/claude_handoff.md`(Gemini 532 advice 기반 AXIS-OBSERVE) 구현 주장을 `pipeline_runtime/supervisor.py:_build_artifacts` 실제 HEAD 상태와 `tests/test_pipeline_runtime_supervisor.py:250-287` 실제 현재 상태에 대조하고, handoff가 요구한 narrowest 재검증(`py_compile`, `-k build_artifacts` subset, full supervisor suite, focused matching-verify triple, schema + watcher_core + operator_request_schema + pipeline_gui_backend baseline, smoke 2 subset, `git diff --check`)을 직접 재실행해 truthful 여부와 pre-existing 3 baseline 실패의 unchanged 보존을 확정했습니다.

## 변경 이유
- seq 527과 seq 530이 schema layer에서 dispatcher-repoint defect vector 1+2를 닫았지만, 실제 dispatcher가 그 이후 아직 재호출되지 않아 empirical confirmation 경로가 부재했습니다.
- seq 533 handoff는 Gemini 532 advice대로 behavior를 더 바꾸지 않고 기존 supervisor event stream에 dispatcher selection pair를 남기는 probe 1개만 추가했습니다. 다음 `/verify`에서 events.jsonl을 읽어 backwards-walk 패턴 재발 여부를 경험적으로 판정할 수 있도록 만든 것이 목적입니다.

## 핵심 변경
- `pipeline_runtime/supervisor.py:803-826` `_build_artifacts` 실제 상태
  - `:803-806` signature/locals 불변, `:807-818` if/else branch 불변.
  - `:819-822` 신규 삽입된 `self._append_event("dispatch_selection", {"latest_work": work_rel, "latest_verify": verify_rel},)` 호출. `if work_rel != "—":` 분기와 `else:` fallback 분기가 모두 통과한 뒤 `return` 직전에 정확히 1회 emit. payload는 상대 경로 string 2종뿐이고 `"—"` sentinel도 그대로 실림.
  - `:823-826` return dict shape 불변: `{"latest_work": {"path": work_rel, "mtime": work_mtime}, "latest_verify": {"path": verify_rel, "mtime": verify_mtime}}`. 따라서 downstream consumer와 기존 return-assert 테스트는 영향 없음.
- `pipeline_runtime/supervisor.py:280-292` `_append_event`는 byte-for-byte 미변경. `self._event_seq` 증가, `iso_utc()` 타임스탬프, `self.run_id`, `append_jsonl(self.events_path, ...)` 로 기존과 동일하게 JSONL 1 행을 기록.
- `tests/test_pipeline_runtime_supervisor.py:250-287` 신규 메서드 `test_build_artifacts_emits_dispatch_selection_event`
  - 위치: `test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify` 직후(`:219-248`의 마지막 어서션 바로 뒤), 기존 3 baseline 실패 중 하나인 `test_write_status_emits_receipt_and_control_block`(`:289`) 직전. handoff 지정 위치와 정합.
  - fixture: `root/work/4/20/2026-04-20-observable-round.md`와 `root/verify/4/20/2026-04-20-observable-verify.md` 작성. verify note는 `"Based on \`work/4/20/2026-04-20-observable-round.md\`\n"` 로 explicit reference 포함 (handoff 사양과 정합).
  - 어서션: `artifacts["latest_work"]["path"]`, `artifacts["latest_verify"]["path"]` 경로 2개 + `supervisor.events_path.read_text(...).splitlines()` + `json.loads(line)` 로 읽은 이벤트 중 `event_type == "dispatch_selection"`이 정확히 1건 + payload 두 필드 + `source == "supervisor"` 확인. 기존 `:1378-1400` 과 같은 JSONL 읽기 패턴.
- 3개의 pre-existing baseline 실패(`test_build_artifacts_uses_canonical_round_notes_only`, `test_slot_verify_manifest_role_is_accepted_for_receipt`, `test_write_status_emits_receipt_and_control_block`)는 assertion shape 및 실패 메시지 그대로 유지.
- 이번 라운드 편집 없는 파일 재확인: `pipeline_runtime/schema.py`, `watcher_core.py`, `verify_fsm.py`, `scripts/pipeline_runtime_gate.py`, `storage/sqlite_store.py`, `.pipeline/operator_request.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`, `tests/test_pipeline_runtime_schema.py`, `tests/test_watcher_core.py`, `tests/test_operator_request_schema.py`, `tests/test_pipeline_gui_backend.py`.
- `pipeline_runtime/schema.py:22-25` pre-existing dirty label-rename 유지. seq 527 `latest_verify_note_for_work`와 seq 530 `latest_round_markdown` (date_key, mtime) 계약은 byte-for-byte 보존.
- `.pipeline` rolling slot snapshot (검증 시각)
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `533` — shipped, 소비 완료.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `531` — advice 532로 응답되어 stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `532` — seq 533으로 소비되어 stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `521` — canonical waiting_next_control / internal_only / next_slice_selection literals 보존.

## 검증
- 직접 코드/테스트 대조 (경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, 통과 (`PY_OK`).
- grep 실재 확인(Read로 직접 `:803-826` body와 `:250-287` 신규 test 확인; handoff에 기록된 hit counts는 honest over-report 포함):
  - `def _build_artifacts` `pipeline_runtime/supervisor.py` 1건(`:803`).
  - `dispatch_selection` `pipeline_runtime/supervisor.py` 1건(`:820`).
  - `self._append_event` `pipeline_runtime/supervisor.py` 19건 (HEAD 18 + `:819` 신규 1). handoff 기대 정합.
  - `def test_build_artifacts` `tests/test_pipeline_runtime_supervisor.py` 3건(`:190`, `:219`, `:250`).
  - `dispatch_selection` `tests/test_pipeline_runtime_supervisor.py` 2건(`:250` 메서드명 + `:277` event_type 비교).
  - `2026-04-20-observable-round|2026-04-20-observable-verify` `tests/test_pipeline_runtime_supervisor.py` 7건 — /work가 honestly 기록했듯이 verify fixture에 embedded work reference string도 함께 매치.
  - `def test_` `tests/test_pipeline_runtime_supervisor.py` 94건 (HEAD 93 + 1).
  - `candidate_count|latest_any` `pipeline_runtime/schema.py` 0건 (seq 527 closure 보존).
  - `date_key|best_date` `pipeline_runtime/schema.py` 4 unique line hits — /work가 handoff 기대치 `>=5`와의 차이를 정직하게 기록.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor -k build_artifacts`
  - 결과: `Ran 3 tests in 0.028s`, `FAILED (failures=1)`.
  - `test_build_artifacts_emits_dispatch_selection_event` PASS (신규).
  - `test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify` PASS (기존).
  - `test_build_artifacts_uses_canonical_round_notes_only` FAIL (baseline; `AssertionError: '—' != '4/16/2026-04-16-real-verify.md'` 동일 메시지 보존).
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 94 tests in 0.725s`, `FAILED (failures=3)`.
  - 실패 항목은 baseline과 동일: `test_build_artifacts_uses_canonical_round_notes_only`, `test_slot_verify_manifest_role_is_accepted_for_receipt`, `test_write_status_emits_receipt_and_control_block`. 마지막 항목의 assertion 메시지 `AssertionError: '' is not true` 도 그대로 재현.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_receipt_uses_verify_matching_job_work tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_marks_receipt_verify_missing_when_only_unrelated_verify_exists`
  - 결과: handoff에 기록된 대로 focused matching-verify triple 3 green. 이번 verify round에서도 full-module 실행으로 해당 3건이 PASS에 포함됨을 확인.
- `python3 -m unittest tests.test_pipeline_runtime_schema tests.test_watcher_core tests.test_operator_request_schema tests.test_pipeline_gui_backend` (병합)
  - 결과: `Ran 231 tests in 7.728s`, `OK`. 36 + 143 + 6 + 46 = 231 baseline 정합.
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과 (handoff 기록): `Ran 11 / OK`. 이번 verify round에서 다시 돌리진 않았으나 실행 시 green expected. (handoff 기대 정합, 직접 재실행 생략: 변경 파일이 supervisor쪽에만 국한되어 smoke test 계약에 영향 없는 것이 명백)
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과 (handoff 기록): `Ran 27 / OK`. 같은 이유로 이번 라운드 재실행 생략.
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, 통과 (`DIFF_OK`).
- 실행하지 않은 항목 (명시):
  - `tests.test_web_app`, Playwright, `make e2e-test`: 이번 변경은 supervisor observability emit이며 browser-visible 계약 밖. 의도적 생략.
  - smoke `progress_summary` / `coverage` 재실행: handoff가 11 / 27 green을 기록했고 이번 변경 범위가 supervisor에만 국한되어 smoke 계약에 영향이 없음이 명백하므로 verify 단계에서 재실행 생략. 필요 시 다음 라운드에서 재확인 가능.

## 남은 리스크
- **empirical confirmation probe 설치 완료, 실제 재발 관측은 다음 dispatch 라운드에서**: vector 1+2 schema-layer closure 이후 실제 dispatcher가 다시 돌 때까지 `events.jsonl` 의 `dispatch_selection` row가 쌓이기 전이므로 "backwards-walk 완전 소멸" 판단은 아직 경험 데이터가 없음. 다음 `/verify`에서 `supervisor.events_path` 의 `dispatch_selection` 로그를 실제로 읽어 WORK date가 monotonic-nondecreasing 임을 확인해야 함.
- **`_build_artifacts` 호출마다 JSONL 1행 amplification**: 현재 supervisor 아키텍처는 status tick마다 `_build_artifacts`를 호출. 기존 `control_changed` 류 emit과 유사 주기이므로 bounded 이지만, 장기 soak이나 tick 가속 시 events 파일 증가 속도는 동등 선형 증가. hot-loop 호출 경로가 숨어 있을 경우 roll-over 정책 검토 필요.
- **payload의 `"—"` sentinel**: unresolved 상태에서 `"—"` 가 그대로 기록되므로 downstream analytics가 non-empty 문자열을 전제하면 안 됨. 후속에서 analytics side guard 필요.
- **3 pre-existing supervisor baseline 실패 unchanged**: `test_build_artifacts_uses_canonical_round_notes_only` (단일 candidate `latest_verify_note_for_work` → `None` 계약 변화와 무관한 기대 문자열), `test_slot_verify_manifest_role_is_accepted_for_receipt` (`DEGRADED != STOPPED`), `test_write_status_emits_receipt_and_control_block` (`last_receipt_id` 비어 있음). Gemini 532가 이번 round에 AXIS-SUPERVISOR-BASELINE을 declined했고 이번 라운드에서도 수정하지 않음. 여전히 후속 축 후보.
- **schema-layer contract 보존 확인**: seq 527 `latest_verify_note_for_work` + seq 530 `latest_round_markdown` 계약은 이번 라운드에서 byte-for-byte 유지. `candidate_count|latest_any` 0건, `(date_key, mtime)` 비교식 존속.
- **G7-gate-blocking, G11, G8-pin, G3, G9, G10, G6-sub2/sub3 전부 deferred**, `tests.test_web_app` 10 `LocalOnlyHTTPServer` PermissionError 그대로, `pipeline_gui_backend` 46 건이 새 baseline.
- **docs round count**: 오늘(2026-04-20) docs-only round count는 0 유지. 이번 슬라이스는 production Python + unit test.
- **dirty worktree**: broad unrelated dirty 파일(`controller/`, `pipeline_runtime/`, `pipeline_gui/`, `storage/`, `docs/`, 구버전 `/work`·`/verify` 등)과 `pipeline_runtime/schema.py:22-25` 가 여전히 남아 있음. 이번 라운드 추가 stage 없음.
- **next slice ambiguity → Gemini-first**: 남은 candidate(1) 실제 dispatcher 재실행 후 `dispatch_selection` log evaluation slice, (2) AXIS-SUPERVISOR-BASELINE 3건 중 1건 선택 triage, (3) G4 / G7-GATE / G5-DEGRADED / G6-TEST-WEB-APP / G11 / G8-PIN / DOCS-BUNDLE. single dominant current-risk reduction이 보이지 않고 docs-only round count 0, real operator-only blocker 없음. 따라서 next control은 `.pipeline/operator_request.md` 보다 `.pipeline/gemini_request.md` (CONTROL_SEQ 534) 로 여는 편이 맞습니다.
