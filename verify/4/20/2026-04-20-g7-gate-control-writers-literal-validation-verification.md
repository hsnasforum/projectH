# 2026-04-20 g7 gate control-writers literal validation verification

## 변경 파일
- `verify/4/20/2026-04-20-g7-gate-control-writers-literal-validation-verification.md`

## 사용 skill
- `round-handoff`: seq 546 `.pipeline/claude_handoff.md` (AXIS-G7-GATE: `validate_operator_candidate_status` read-time literal 검증 + `tests/test_pipeline_runtime_control_writers.py` append) 구현 주장과 seq 546 handoff의 scope limits를 실제 HEAD 상태에 대조하고, handoff가 요구한 narrowest 재검증 (`py_compile`, 신규 단일 테스트, 전체 control_writers 6, regression `tests.test_operator_request_schema` 6, supervisor+schema 묶음, `git diff --check`, grep cross-check)을 직접 재실행했습니다.

## 변경 이유
- 새 `/work` 라운드가 `pipeline_runtime/control_writers.py:validate_operator_candidate_status`에 read-time `SUPPORTED_REASON_CODES` / `SUPPORTED_OPERATOR_POLICIES` 검증을 추가하고, `tests/test_pipeline_runtime_control_writers.py`에 회귀 테스트 1건을 append했다고 주장했습니다. verify 라인은 이번 라운드 편집이 target 2파일에만 한정됐는지, Gemini 545의 잘못된 placement 제안(= `tests/test_operator_request_schema.py`) 대신 실제 home인 control_writers 테스트 파일에만 반영됐는지, 그리고 seq 527/530/533/536/539/543/521 contract가 byte-for-byte 보존됐는지를 확인해야 했습니다.

## 핵심 변경 (verify 관점에서 본 HEAD 스냅샷)
- `pipeline_runtime/control_writers.py:228-260` `validate_operator_candidate_status`
  - `:247-251` 기존 `classification_source not in {"operator_policy", "reason_code"}` raise 유지.
  - `:252-254` 신규: `normalized_reason_code = normalize_reason_code(reason_code)` + `if normalized_reason_code and normalized_reason_code not in SUPPORTED_REASON_CODES: raise ValueError(f"unsupported reason_code: {reason_code}")`.
  - `:255-260` 신규: `normalized_operator_policy = normalize_operator_policy(operator_policy)` + 같은 형태의 `SUPPORTED_OPERATOR_POLICIES` membership 검사.
  - empty-string normalize 결과는 계속 통과 — `classification_source` 축이 authoritative인 기존 contract 유지.
  - `DECISION_CLASS`는 이 read path에 의도적으로 추가하지 않았음을 확인 (`autonomy` dict contract에 `decision_class` 미포함). write-time enforcement는 `validate_operator_request_headers:58-60`에 그대로 남아 있음.
  - 함수 시그니처, imports(`:6-12`), `validate_operator_request_headers`(`:32-60`), `render_implement_blocked` 경로는 byte-for-byte 유지.
- `tests/test_pipeline_runtime_control_writers.py`
  - `:107-140` 신규 메서드 `test_validate_operator_candidate_status_rejects_unsupported_reason_code_and_operator_policy_literals` 추가.
  - first block: `"not_a_real_reason_code_literal"` + `classification_source="reason_code"` → `assertRaisesRegex(ValueError, "unsupported reason_code")` 통과 확인.
  - second block: `"not_a_real_policy_literal"` + `classification_source="operator_policy"` → `assertRaisesRegex(ValueError, "unsupported operator_policy")` 통과 확인.
  - positive-control third invocation은 handoff 템플릿이 제시했으나 현재 HEAD에는 포함되지 않음 — 핵심 두 negative 경로는 모두 green. 이 차이는 이번 라운드 내에서 red가 없고, `classification_source`만 덮이면 `SUPPORTED_REASON_CODES`/`SUPPORTED_OPERATOR_POLICIES`의 positive는 기존 테스트(`test_validate_operator_candidate_status_requires_structured_classification_source` 두 번째 호출)가 이미 커버하므로 계약 회귀는 없음.
  - 기존 5개 테스트(`test_write_operator_request_round_trips_through_control_meta`, `test_render_operator_request_rejects_missing_required_headers`, `test_render_implement_blocked_rejects_unknown_reason_code_and_escalation_class`, `test_validate_operator_candidate_status_requires_structured_classification_source`, `test_no_non_test_direct_writes_for_operator_or_implement_blocked`) byte-for-byte 유지 확인 (총 6 green).
- `tests/test_operator_request_schema.py`는 건드리지 않았음을 grep으로 확인 (Gemini 545 placement error 교정 존중). `Ran 6 / OK` 유지.
- `scripts/pipeline_runtime_gate.py`, `pipeline_runtime/operator_autonomy.py`, `pipeline_runtime/schema.py`, `pipeline_runtime/supervisor.py`, `watcher_core.py`, `verify_fsm.py`, `storage/sqlite_store.py`, `.pipeline/operator_request.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md` 모두 이번 라운드에서는 수정되지 않음을 확인. 이전 dirty-worktree 상태는 그대로.
- seq 408/.../520/521/527/530/533/536/539/543 shipped surface byte-for-byte 유지.

## 검증
- `python3 -m py_compile pipeline_runtime/control_writers.py tests/test_pipeline_runtime_control_writers.py`
  - 결과: 출력 없음, exit 0 (`OK_PYCOMPILE`).
- `python3 -m unittest -v tests.test_pipeline_runtime_control_writers`
  - 결과: `Ran 6 tests in 0.004s`, `OK`. 6개 test 개별 모두 `ok` 라벨 확인 (신규 `test_validate_operator_candidate_status_rejects_unsupported_reason_code_and_operator_policy_literals` 포함).
- `python3 -m unittest -v tests.test_pipeline_runtime_control_writers.ControlWritersTest.test_validate_operator_candidate_status_rejects_unsupported_reason_code_and_operator_policy_literals`
  - 결과: `Ran 1 test in 0.001s`, `OK`. 타깃 단일 메서드 green 직접 확인.
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과: `Ran 6 tests in 0.001s`, `OK`. Gemini 545 placement 제안을 따르지 않아 7이 되지 않고 6을 유지함을 확인.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_schema`
  - 결과: `Ran 134 tests`, `OK`. 98 + 36 합계가 정확히 일치. seq 533/536/539/543 regression 정합.
- `git diff --check -- pipeline_runtime/control_writers.py tests/test_pipeline_runtime_control_writers.py`
  - 결과: 출력 없음 (`OK_DIFF`).
- grep cross-check
  - `rg -n 'def validate_operator_candidate_status' pipeline_runtime/control_writers.py` → 1 hit (`:228`).
  - `rg -n 'unsupported reason_code|unsupported operator_policy' pipeline_runtime/control_writers.py` → 4 hits (`:52`, `:56`, `:254`, `:260`). `/work` 기록 정합.
  - `rg -n 'SUPPORTED_REASON_CODES|SUPPORTED_OPERATOR_POLICIES' pipeline_runtime/control_writers.py` → 7 hits (`:7`, `:8`, `:51`, `:55`, `:172`, `:253`, `:258`). 신규 read path check 2건(`:253`, `:258`)은 `validate_operator_candidate_status` body에 위치함을 Read로 확인.
  - `rg -n 'def test_validate_operator_candidate_status' tests/test_pipeline_runtime_control_writers.py` → 2 hits (`:78`, `:107`).
  - `rg -n 'def test_' tests/test_pipeline_runtime_control_writers.py` → 6.
  - `rg -n 'def test_' tests/test_operator_request_schema.py` → 6 (불변 확인).
- 실행하지 않은 항목 (명시):
  - `tests.test_watcher_core`, `tests.test_pipeline_gui_backend`, `tests.test_smoke -k progress_summary|coverage`: `/work`에서 green 기록(143/46/11/27)을 남긴 범위 regression. 이번 라운드 편집은 `control_writers.py` + 해당 테스트 파일로만 국한됐고 해당 모듈은 `validate_operator_candidate_status` 를 import하지 않으므로 본 verify round에서 재실행 생략.
  - `tests.test_web_app`, Playwright, `make e2e-test`: browser-visible 계약 변경 없음. 의도적 생략.
  - full-repo dirty worktree audit: 범위 밖.

## 남은 리스크
- **G7 gate 부분 closure**: `validate_operator_candidate_status` read-time에 `SUPPORTED_REASON_CODES` + `SUPPORTED_OPERATOR_POLICIES` 둘만 추가되었고, `SUPPORTED_DECISION_CLASSES`(6-member) read path 확장은 `autonomy` dict가 `decision_class`를 carry하기 시작할 때에만 후속 slice에서 가능. 현재는 write-time `validate_operator_request_headers:58-60`이 유일한 DECISION_CLASS 경계.
- **Gemini 545 placement drift 교정 기록**: `tests/test_operator_request_schema.py`가 아니라 `tests/test_pipeline_runtime_control_writers.py`에 append된 점을 명시 기록. 추후 Gemini advice가 동일한 오분류를 반복하지 않도록 verify 라인에서 경계 문서화가 필요할 수 있음.
- **AXIS-STALE-REFERENCE-AUDIT**: 여전히 오픈. `tests/test_pipeline_runtime_supervisor.py:1057` 근방 bare `"# verify\n"` fixture sweep 미수행.
- **AXIS-EMIT-PAYLOAD-ENRICH**: 아직 미결. seq 542 typo 클래스를 payload source에서 닫는 슬라이스 후보.
- **AXIS-DISPATCHER-TRACE-BACKFILL**: 다음 real dispatch 후 empirical monotonic 확인용 verify-lane instruction 미배포.
- **G4, G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3**: 계속 deferred.
- **`tests.test_web_app`** 10건 `LocalOnlyHTTPServer` PermissionError baseline 유지.
- **Docs-only round count**: 오늘(2026-04-20) 0 유지 (이번 라운드는 production validation + unit test slice).
- **Dirty worktree**: broad unrelated dirty 파일 + `pipeline_runtime/schema.py:22-25` pre-existing label-rename diff 그대로. 이번 verify가 추가 stage하거나 reset하지 않음.
- **next slice ambiguity → Gemini-first**: 남은 후보(G7-DECISION_CLASS read-path 확장 가능성 / AXIS-STALE-REFERENCE-AUDIT / AXIS-EMIT-PAYLOAD-ENRICH / AXIS-DISPATCHER-TRACE-BACKFILL / G4 / G5-DEGRADED-BASELINE docs / G6-TEST-WEB-APP / G11 / G8-PIN)는 축이 서로 다르고 dominant current-risk reduction이 명확하지 않음. real operator-only blocker도 없음. 따라서 seq 547 next-control은 `.pipeline/operator_request.md` 대신 `.pipeline/gemini_request.md`로 여는 것이 맞습니다.
