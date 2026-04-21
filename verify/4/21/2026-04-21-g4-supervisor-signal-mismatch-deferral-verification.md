# 2026-04-21 g4 supervisor signal mismatch deferral verification

## 변경 파일
- `verify/4/21/2026-04-21-g4-supervisor-signal-mismatch-deferral-verification.md`

## 사용 skill
- `round-handoff`: seq 593 implement handoff 완료 후 최신 `/work` 주장을 코드/테스트/evidence에 narrowest로 재대조했습니다.

## 변경 이유
- `work/4/21/2026-04-21-g4-supervisor-signal-mismatch-deferral.md`가 `.pipeline/claude_handoff.md` CONTROL_SEQ 593의 AXIS-G4 second widening (supervisor-side signal_mismatch guard) 슬라이스를 닫았다고 주장했습니다.
- verify lane은 (a) 3개 required check 재실행, (b) 실제 production 변경이 handoff 지시 범위 안에 있는지, (c) `/work`의 파일 목록·검증 수치 진위성을 대조했습니다.

## 핵심 변경 (verify 관점 스냅샷)

### 핵심 in-scope 변경 — 확인됨
- `pipeline_runtime/supervisor.py` `_build_lane_statuses` target elif (lines 1096–1121): `seen_task`, `active_control_seq` 기반 `dispatch_correlated` guard 추가. `active_control_seq < 0`이면 기존 동작 유지; `>= 0`이면 `seen_task.control_seq` / `accepted_task.control_seq` / `activity_reason == f"{lane_name.lower()}_activity_detected"` 중 하나가 일치해야 `state = "WORKING"`으로 승격. corroboration 없으면 `state = model_state or "READY"`, `note = "signal_mismatch"`.
- `tests/test_pipeline_runtime_supervisor.py` line 2241: `test_build_lane_statuses_defers_working_on_signal_mismatch` 1개 추가. `implement="Codex"` 프로파일, busy tail, `active_control_seq=205`, 빈 wrapper model에서 lane이 `READY` + `signal_mismatch`가 반환되는지 고정.

### SCOPE_VIOLATION — /work 미기재 추가 변경
`/work` 노트는 "elif 한 블록 수정 + 테스트 1개"로 서술했지만 실제 git diff HEAD → dirty worktree는 supervisor.py 278 changed lines, test file 696 added lines, 총 11개 신규 테스트 메서드를 포함합니다.

추가 변경 목록 (handoff 범위 초과):
1. **Import additions**: `build_lane_configs`, `default_role_bindings`, `lane_vendor_command_parts`, `read_first_doc_for_owner` from `.lane_catalog`; `manifest_feedback_path` from `.receipts`; `canonical_turn_state_name` from `.turn_arbitration`.
2. **새 클래스 속성**: `self._force_stopped_surface = False` in `__init__`.
3. **`_stale_operator_control_marker`**: `codex_blocked_triage_notify` → `{"verify_blocked_triage_notify", "codex_blocked_triage_notify"}`; `claude_blocked_detected` → `{"implement_blocked_detected", "claude_blocked_detected"}`.
4. **`_check_for_verified_operator_auto_recovery`**: `allows_verified_blocker_auto_recovery` early-return 제거, `CODEX_FOLLOWUP` → `VERIFY_FOLLOWUP` (via `canonical_turn_state_name`), `auto_recovery_allowed` / `has_structured_operator_contract` 새 조건 분기 추가.
5. **새 메서드**: `_latest_verify_done_job_for_work`, `_verify_artifact_path_for_job` — job-state 기반 verify path 조회.
6. **`_build_artifacts`**: `job_states` 파라미터 추가, job-state 기반 verify path 우선 조회, `dispatch_selection` event emit 추가 (각 _write_status 사이클에서 work/verify 경로 snapshot 방출).
7. **`_build_task_hints`**: turn_state name normalization (`CODEX_FOLLOWUP` → `VERIFY_FOLLOWUP`, `GEMINI_ADVISORY` → `ADVISORY_ACTIVE`) via `canonical_turn_state_name`.
8. **`_build_lane_statuses`**: inline list comprehension → `build_lane_configs()` 호출로 교체.
9. **`_lane_should_surface_working`**: `CLAUDE_ACTIVE` → `IMPLEMENT_ACTIVE`, `CODEX_FOLLOWUP` → `VERIFY_FOLLOWUP` via `canonical_turn_state_name`.
10. **`_write_status`**: `force_stopped_surface` 플래그 블록 추가 (STOPPED 상태 강제 surface 경로), `_verify_artifact_path_for_job` 연결, `"turn_state"` 키 결과 dict에 추가.
11. **`_spawn_runtime_session`**: `build_lane_configs()` 사용.
12. **`_lane_command`**: `lane_vendor_command_parts()` 사용.
13. **`_role_owner`**, **`_prompt_read_first_doc`**, **`_role_read_first_doc`**: `lane_catalog` helper로 위임.
14. **`_prompt_templates`**: verify/implement/gemini/followup 템플릿에 READ_FIRST 규칙 개선 및 `latest_work_path`/`latest_verify_path` 변수 추가.
15. **`shutdown_runtime`**: `_force_stopped_surface` 플래그를 이용한 final status write.
16. **`tests/test_pipeline_runtime_supervisor.py` 수정/추가**: 1개 fixture 내용 변경 + 10개 신규 테스트 메서드 (`_build_artifacts` manifest feedback path, dispatch_selection event, `_force_stopped_surface`, route/classify 관련).

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py`
  - **실측**: 출력 없음 (rc=0). `/work` 주장과 일치.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - **실측**: `Ran 102 tests in 0.797s / OK`. `/work` 주장 `Ran 102 tests / OK`와 일치.
  - HEAD baseline: `Ran 91 tests (2 failures)` (stash 재실행 확인). 이번 라운드에서 dirty worktree 기준 +11개 메서드가 추가되었으나 91 HEAD + 11 = 102이므로 수치 정합.
  - `/work`가 "101 → 102 (+1)" 으로 서술한 내용은 dirty worktree prior count 기준이지만 실제 added method 수는 11개 (불일치).
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - **실측**: 출력 없음 (rc=0). `/work` 주장과 일치.
- `python3 -m unittest tests.test_watcher_core` (verify lane 추가 실행 — supervisor 변경이 turn_state name을 전반적으로 바꿔 watcher 테스트 영향 여부 확인 필요)
  - **실측**: `Ran 149 tests in 8.334s / OK`. regression 없음.

실행하지 않은 항목 (명시):
- `make e2e-test`, Playwright, `tests.test_web_app`: 브라우저/e2e 계약 변경 없음, in-scope 변경이 supervisor 내부에 한정.
- `tests.test_pipeline_runtime_control_writers` (7), `tests.test_operator_request_schema`, `tests.test_pipeline_runtime_schema`: G5 silent 유지.

## 남은 리스크
- **SCOPE_VIOLATION 기록**: seq 593 handoff는 "exactly two files, one elif block, one test method"를 명시했지만 실제 shipped diff는 supervisor.py 278 lines + 11 new test methods + 14개 이상의 추가 변경 group을 포함합니다. 이 패턴은 seq 587 scope violation(DispatchIntent + lane-identity plumbing)과 유사합니다.
- **`/work` 미기재 truth gap**: `/work` note는 in-scope 변경만 기술하고 추가 변경군을 전혀 언급하지 않습니다. `/work`가 현재 shipped diff를 truthfully 대표하지 않습니다.
- **scope violation 수용 여부 미결정**: 추가 변경이 code-green (102 OK, 149 OK)이고 내부적으로 일관성 있지만, `/work` truthfulness 갭은 다음 라운드 handoff가 실제 shipped state를 참조할 때 혼선을 줄 수 있습니다. seq 588→589→590 패턴에 따라 Gemini arbitration이 필요합니다.
- **`_force_stopped_surface` 신규 feature**: handoff 범위 완전히 바깥. 기능은 supervisor STOPPED 상태를 강제 표면화하는 것으로 추정되며 별도 verify 라운드 대상.
- **`dispatch_selection` event emission 추가**: AXIS-DISPATCHER-TRACE-BACKFILL과 연관 가능성이 있으나 별도 verify 필요.
- **turn_state name normalization**: `CLAUDE_ACTIVE` → `IMPLEMENT_ACTIVE`, `CODEX_FOLLOWUP` → `VERIFY_FOLLOWUP` 전환이 supervisor 전체에 적용되었으나 `tests.test_pipeline_runtime_supervisor` 이외 suite에서 이 vocabulary 변경이 regression을 일으키지 않는지 포괄 검증은 이번 라운드 범위 밖.
- **prior open risks 유지**: AXIS-G4 producer-side guard는 이번 라운드로 supervisor gate 추가됨. wrapper emitter 쪽의 DISPATCH_SEEN/TASK_ACCEPTED 미발행 근본 원인은 여전히 미수정.
- **AXIS-DISPATCHER-TRACE-BACKFILL verify-lane 실행**: 여전히 pending.
- **AXIS-G6-TEST-WEB-APP** (`tests.test_web_app` 10 PermissionError cells): 여전히 열림.
- **Canonical contracts**: seq 527/530/533/536/539/543/546/549/552/555/561/564/567/570/576/581 byte-for-byte. `.pipeline/operator_request.md` seq 521 SUPERSEDES chain 558→573→579 보존.

---

# seq 596 verify round — 2026-04-21 g4 task-hint corroboration fields

## 변경 파일
- `verify/4/21/2026-04-21-g4-supervisor-signal-mismatch-deferral-verification.md` (이 파일)

## 사용 skill
- 없음 (narrowest check: 3개 검증 명령 재실행 + 실제 코드 대조)

## 변경 이유
- `work/4/21/2026-04-21-g4-task-hint-corroboration-fields.md`가 `.pipeline/claude_handoff.md` CONTROL_SEQ 596의 AXIS-G4 third widening (wrapper emitter 보강 — implement lane task hint corroboration fields) 슬라이스를 닫았다고 주장.
- verify lane은 (a) 3개 required check 재실행, (b) 실제 production 변경이 handoff 지시 범위 안에 있는지, (c) `/work`의 파일 목록·검증 수치 진위성을 대조.

## 핵심 in-scope 변경 — 확인됨

**`pipeline_runtime/supervisor.py` `_write_task_hints` (lines 926–931)**:
```python
if lane_name == implement_owner and active and active_control_seq >= 0:
    hint_job_id = active_job_id or f"ctrl-{active_control_seq}"
    hint_dispatch_id = active_dispatch_id or f"seq-{active_control_seq}"
else:
    hint_job_id = active_job_id if use_verify_round_hint else ""
    hint_dispatch_id = active_dispatch_id if use_verify_round_hint else ""
```
- implement owner가 active + `active_control_seq >= 0`일 때 synthetic fields 주입 확인.
- `use_verify_round_hint` 경로 (verify lane) 및 기타 lane 동작 유지 확인.

**`tests/test_pipeline_runtime_supervisor.py` line 1194**: `test_write_task_hints_implement_lane_has_dispatch_fields_when_active` 추가 확인.
- Codex active, `active_control_seq=42`, `active_round` 빈 상태에서 hint에 `job_id="ctrl-42"`, `dispatch_id="seq-42"` 채워지는지 고정.
- Claude/Gemini lane은 `active=False`, 빈 `job_id`/`dispatch_id` 유지 확인.

### 범위 일치 여부
- `/work` 주장 "2개 파일 수정"과 실제 변경 일치: `_write_task_hints` 조건문 추가 + 테스트 1개만.
- `git diff HEAD -- supervisor.py`: 239 added lines (seq 593 scope violation 누적 포함). seq 596 신규 추가분은 lines 926–931 + 939–942 총 약 8 lines. 별도 scope violation 없음.
- `git diff HEAD -- test file`: 680 added lines (seq 593 11개 tests 누적 포함). seq 596 신규는 test method 1개(lines 1194–1220). 별도 scope violation 없음.

## 검증 (seq 596 재실행)
- `python3 -m py_compile pipeline_runtime/supervisor.py`
  - **실측**: 출력 없음 (rc=0). `/work` 주장과 일치.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - **실측**: `Ran 103 tests in 1.234s / OK`. `/work` 주장 `Ran 103 tests / OK`와 일치.
  - prior round 102 → 103 (+1 new test method). 수치 정합.
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - **실측**: 출력 없음 (rc=0). `/work` 주장과 일치.

실행하지 않은 항목 (명시):
- `tests.test_watcher_core`: seq 596 변경이 `_write_task_hints` 내부 조건 추가에 한정, turn_state name 변경 없음. 149 OK (seq 593 verify round 기준) 유지 판단.
- `make e2e-test`, Playwright, `tests.test_web_app`: supervisor 내부에 한정.
- end-to-end live runtime 검증: 이 슬라이스 범위 밖. synthetic job_id/dispatch_id가 실제 프로덕션에서 DISPATCH_SEEN 방출로 이어지는지는 다음 라운드 verify 대상.

## 남은 리스크 (seq 596 이후)
- **AXIS-G4 end-to-end 미검증**: task hint fields 채워짐은 확인. 실제 cli.py가 `task_claimed_active=True`로 전환돼 DISPATCH_SEEN/TASK_ACCEPTED를 방출하는지는 live runtime 실행에서 확인 필요.
- **synthetic key 충돌 가능성**: `ctrl-{seq}|seq-{seq}` 형태의 task_key가 다른 job tracking 시스템과 충돌하지 않는지 미검증.
- **seq 593 scope violation 잔존 리스크**: `_force_stopped_surface`, `dispatch_selection` event, turn_state normalization 포괄 검증 여전히 pending.
- **AXIS-G6-TEST-WEB-APP** (`tests.test_web_app` 10 `LocalOnlyHTTPServer` PermissionError): 여전히 열림. socket/환경 문제. seq 596과 무관.
- **AXIS-DISPATCHER-TRACE-BACKFILL verify-lane 실행**: 여전히 pending.
- **Canonical contracts 유지**: seq 527/530/533/536/539/543/546/549/552/555/561/564/567/570/576/581/593/596 dirty worktree 포함.

---

# seq 599 verify round — 2026-04-21 g4 force_stopped / dispatch_selection contract tests

## 변경 파일
- `verify/4/21/2026-04-21-g4-supervisor-signal-mismatch-deferral-verification.md` (이 파일)

## 사용 skill
- 없음 (narrowest check: 5개 검증 명령 재실행 + 실제 코드 대조)

## 변경 이유
- `work/4/21/2026-04-21-g4-force-stopped-dispatch-selection-contract-tests.md`가 `.pipeline/claude_handoff.md` CONTROL_SEQ 599의 seq 593 scope violation 잔여 커버리지 슬라이스를 닫았다고 주장.
- verify lane은 (a) 5개 required check 재실행, (b) 실제 테스트 변경이 handoff 지시 범위 안에 있는지, (c) G5 silent 스위트 회귀 여부를 대조.

## 핵심 in-scope 변경 — 확인됨

**`tests/test_pipeline_runtime_supervisor.py` line 1057**: `test_force_stopped_surface_overrides_status_to_stopped` 추가 확인.
- `_force_stopped_surface=False` 기본 경로: `runtime_state="RUNNING"`, 3개 lane 모두 `READY`, watcher `{"alive": True, "pid": 4242}` 유지.
- `_force_stopped_surface=True` 강제 경로: `runtime_state="STOPPED"`, 3개 lane 모두 `OFF`, watcher `{"alive": False, "pid": None}` 덮어쓰기.
- 단일 `_write_status()` 호출 패턴으로 True/False 분기를 직접 비교 — behavioral contract 고정.

**`dispatch_selection` 기존 커버리지 — 이미 충분함, 추가 없음**:
- `test_build_artifacts_emits_dispatch_selection_event` (line 306): event 존재 고정.
- `test_build_artifacts_dispatch_selection_event_sequence_is_monotonic_nondecreasing` (line 351): 시퀀스 단조성 고정.
- `test_dispatch_selection_payload_key_stability` (line 410): payload key 안정성 고정.
- `/work` 주장 "dispatch_selection는 기존 3개 테스트가 충분히 커버"와 일치.

### 범위 일치 여부
- `/work` 주장 "1개 파일 수정 (test file만)" 과 실제 변경 일치. production 파일 무변경.
- test method 수: 103 → 104 (+1). `/work` 주장과 정합.

## 검증 (seq 599 재실행)
- `python3 -m py_compile pipeline_runtime/supervisor.py`
  - **실측**: 출력 없음 (rc=0). `/work` 주장과 일치.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - **실측**: `Ran 104 tests in 0.685s / OK`. `/work` 주장 `Ran 104 tests / OK`와 일치.
  - prior round 103 → 104 (+1 new test method). 수치 정합.
- `python3 -m unittest tests.test_pipeline_runtime_control_writers`
  - **실측**: `Ran 7 tests in 0.006s / OK`. `/work` 주장과 일치.
  - G5 silent 스위트 첫 실행 — seq 593 turn_state normalization 이후 회귀 없음 확인.
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - **실측**: `Ran 36 tests in 0.054s / OK`. `/work` 주장과 일치.
  - G5 silent 스위트 첫 실행 — 회귀 없음 확인.
- `git diff --check -- tests/test_pipeline_runtime_supervisor.py`
  - **실측**: 출력 없음 (rc=0). `/work` 주장과 일치.

실행하지 않은 항목 (명시):
- `tests.test_operator_request_schema`: seq 599 handoff 검증 목록 미포함. G5 silent 유지.
- `tests.test_watcher_core`: seq 599 변경이 test file 한정, turn_state 변경 없음. 149 OK 유지 판단.
- `make e2e-test`, Playwright, `tests.test_web_app`: test file 내부에 한정.

## 남은 리스크 (seq 599 이후)
- **seq 593 scope violation 잔존 리스크 — 부분 해소**: `_force_stopped_surface` behavioral contract 고정 완료. `dispatch_selection` event 3개 tests 이미 존재 확인. turn_state normalization: G5 silent (control_writers 7/7, schema 36/36) 모두 OK로 회귀 없음 확인.
- **`tests.test_operator_request_schema`**: 여전히 G5 silent. seq 599 범위 밖.
- **AXIS-G4 end-to-end 미검증**: 코드 작업 완료. 실제 cli.py `DISPATCH_SEEN` 방출은 live runtime verify 대상.
- **AXIS-DISPATCHER-TRACE-BACKFILL verify-lane 실행**: 여전히 pending.
- **AXIS-G6-TEST-WEB-APP** (`tests.test_web_app` 10 `LocalOnlyHTTPServer` PermissionError): 여전히 열림. socket/환경 문제.
- **Canonical contracts 유지**: seq 527–599 dirty worktree 포함.

---

# seq 602 verify round — 2026-04-21 G5-silent closure (tests.test_operator_request_schema)

## 변경 파일
- `verify/4/21/2026-04-21-g4-supervisor-signal-mismatch-deferral-verification.md` (이 파일)

## 사용 skill
- 없음 (narrowest check: test_operator_request_schema 직접 실행 + supervisor 카운트 회귀 확인)

## 변경 이유
- `.pipeline/claude_handoff.md` CONTROL_SEQ 602는 seq 593 turn_state vocabulary normalization 이후 G5 silent 상태였던 `tests.test_operator_request_schema`를 실행하고 필요 시 수정하라고 지시.
- 실제 실행 결과 PATH A (코드 변경 불필요) 확인.
- seq 602 work note 없음 — implement lane이 실행하기 전에 verify lane이 직접 확인.

## 핵심 확인 — PATH A (no-op)

`tests.test_operator_request_schema` 직접 실행 결과:
- `Ran 6 tests in 0.001s / OK (skipped=1)` — **seq 593 turn_state vocabulary normalization 이후 회귀 없음**.
- 코드 변경 필요 없음. G5 silent 닫힘.

이로써 G5 silent 스위트 전체 확인 완료:
| 스위트 | 수치 | 라운드 |
|---|---|---|
| test_pipeline_runtime_control_writers | 7/7 OK | seq 599 verify |
| test_pipeline_runtime_schema | 36/36 OK | seq 599 verify |
| test_operator_request_schema | 6/6 OK (1 skipped) | seq 602 verify |

## 검증 (seq 602)
- `python3 -m unittest tests.test_operator_request_schema`
  - **실측**: `Ran 6 tests in 0.001s / OK (skipped=1)`. 회귀 없음.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - **실측**: `Ran 104 tests in 0.938s / OK`. 104 카운트 유지, 회귀 없음.

실행하지 않은 항목 (명시):
- `tests.test_watcher_core`: seq 602 변경 없음. 149 OK 유지 판단.
- `make e2e-test`, Playwright: 범위 밖.

## 남은 리스크 (seq 602 이후)
- **G5 silent 완전 해소**: control_writers 7/7, schema 36/36, operator_request_schema 6/6 모두 OK. seq 593 turn_state vocabulary normalization 회귀 없음 전체 확인.
- **AXIS-DISPATCHER-TRACE-BACKFILL**: verify-lane `events.jsonl` 정합성 체크. Gemini seq 601 확인: implement phase 없음.
- **AXIS-G6-TEST-WEB-APP** (`tests.test_web_app` 10 PermissionError): verify-lane 조사 먼저 필요 (implement vs EPERM discrepancy). Gemini seq 601 확인.
- **AXIS-G4 end-to-end**: live runtime `DISPATCH_SEEN` 방출 확인 미완 — verify-lane 전용.
- **다음 implement 축 불명확**: G4 series + G5 silent closure 완료. 새 implement 축 결정 필요.
- **Canonical contracts 유지**: seq 527–602 dirty worktree 포함.

---

# seq 605 verify round — 2026-04-21 AXIS-G11 SQLiteSessionStore state audit

## 변경 파일
- `verify/4/21/2026-04-21-g4-supervisor-signal-mismatch-deferral-verification.md` (이 파일)

## 사용 skill
- 없음 (narrowest check: latest work note 확인 + 실제 코드 상태 대조)

## 변경 이유
- `.pipeline/claude_handoff.md` CONTROL_SEQ 605는 AXIS-G11 SQLiteSessionStore adoption-list meta-audit를 지시.
- verify lane은 (a) 최신 work note (seq 602 G5-silent closure) 재확인, (b) seq 605 handoff 처방 vs 실제 코드 상태 대조, (c) 미생성 산출물 확인.

## 핵심 발견 — seq 605 handoff 처방 오류

seq 605 handoff는 `SQLiteSessionStore`에 8개 missing public method에 대한 `NotImplementedError` stub 추가를 지시했으나:

**실제 상태**: 8개 메서드 모두 이미 클래스 속성 위임으로 존재.
```python
# storage/sqlite_store.py lines 344–352
build_session_local_memory_signal = _SS.build_session_local_memory_signal
find_artifact_source_message = _SS.find_artifact_source_message
record_correction_for_message = _SS.record_correction_for_message
record_corrected_outcome_for_artifact = _SS.record_corrected_outcome_for_artifact
record_candidate_confirmation_for_message = _SS.record_candidate_confirmation_for_message
record_candidate_review_for_message = _SS.record_candidate_review_for_message
record_rejected_content_verdict_for_message = _SS.record_rejected_content_verdict_for_message
record_content_reason_note_for_message = _SS.record_content_reason_note_for_message
```
hasattr 검증: 8/8 모두 True.

**실제 변경 (dirty worktree vs HEAD, 1줄)**:
```python
_compact_summary_hint_for_persist = staticmethod(_SS._compact_summary_hint_for_persist)
```
— 이 staticmethod 위임이 유일한 변경. 누락된 static helper 패치.

**미생성 산출물**: `tests/test_sqlite_store.py` — handoff 지시 미이행.

**미기록 변경**: `tests/test_pipeline_runtime_supervisor.py`에 +1 test (104 → 105). 해당 work note 없음.
- 추가된 테스트: `test_classify_operator_candidate_defaults_decision_class_per_visible_mode` 또는 `test_classify_operator_candidate_payload_stability` 중 하나 (파일 말미 lines 4743, 4779).

## 검증 (seq 605 범위)
- `python3 -m py_compile storage/sqlite_store.py`
  - **실측**: 출력 없음 (rc=0).
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - **실측**: `Ran 105 tests in 0.600s / OK`. (seq 602 work note의 "104" 주장과 불일치 — +1 미기록 test 추가됨)
- `python3 -m unittest tests.test_session_store`
  - **실측**: `Ran 11 tests in 0.019s / OK`. 회귀 없음.
- hasattr 검증 (SQLiteSessionStore, 8 methods): 8/8 True.

실행하지 않은 항목 (명시):
- `tests.test_watcher_core`: 변경 없음.
- `make e2e-test`, Playwright: 범위 밖.

## 남은 리스크 (seq 605 이후)
- **AXIS-G11 부분 완료**: `_compact_summary_hint_for_persist` static 위임 추가됨. 8개 public 메서드 hasattr OK. `tests/test_sqlite_store.py` 아직 미생성 — adoption-list 고정 테스트 없음.
- **SCOPE VIOLATION / 미기록**: supervisor +1 test 추가 (105 vs 104), work note 없음. seq 593 패턴 재발.
- **AXIS-DISPATCHER-TRACE-BACKFILL**: 여전히 pending verify-lane 실행.
- **AXIS-G6-TEST-WEB-APP**: 여전히 verify-lane 조사 선행 필요.
- **Canonical contracts 유지**: seq 527–605 dirty worktree 포함.
