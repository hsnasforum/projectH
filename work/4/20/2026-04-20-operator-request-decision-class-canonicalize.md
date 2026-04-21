# 2026-04-20 operator_request decision class canonicalize

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `tests/test_operator_request_schema.py`

## 사용 skill
- `finalize-lite`: 실제 실행한 검증, doc-sync 필요 여부, `/work` closeout readiness만 묶어 구현 라운드를 마감했습니다.

## 변경 이유
- seq 507에서는 `DECISION_CLASS` vocabulary를 test file 내부 `OBSERVED_DECISION_CLASSES`로만 유지하고 있었고, Gemini 509가 `advisory_only`를 forward-looking canonical member로 명시적으로 포함시키는 결정을 내렸습니다.
- 이번 슬라이스는 runtime behavior는 건드리지 않고, `DECISION_CLASS` vocabulary를 `pipeline_runtime.operator_autonomy`로 승격해 `REASON_CODE` / `OPERATOR_POLICY`와 같은 canonical symbol 형태로 정리하는 가장 작은 follow-up이 목적이었습니다.

## 핵심 변경
- `pipeline_runtime/operator_autonomy.py:53-62`에 `SUPPORTED_DECISION_CLASSES`를 `SUPPORTED_REASON_CODES` 바로 뒤에 추가했습니다. membership은 Gemini 509의 explicit IN decision을 따라 정확히 6개입니다.
  - `operator_only`
  - `advisory_only`
  - `next_slice_selection`
  - `internal_only`
  - `truth_sync_scope`
  - `red_test_family_scope_decision`
- `pipeline_runtime/operator_autonomy.py:174-175`의 `normalize_decision_class`는 수정하지 않았습니다. runtime behavior는 그대로 pass-through이며, 이번 라운드는 canonical symbol 추가만 수행했습니다.
- `tests/test_operator_request_schema.py:4-8`은 이제 `SUPPORTED_DECISION_CLASSES`, `SUPPORTED_OPERATOR_POLICIES`, `SUPPORTED_REASON_CODES`를 모두 `pipeline_runtime.operator_autonomy`에서 import합니다.
- `tests/test_operator_request_schema.py`의 inline `OBSERVED_DECISION_CLASSES` frozenset과 그 comment는 완전히 제거했습니다.
- `tests/test_operator_request_schema.py:70-74`에서 `test_decision_class_is_observed`를 `test_decision_class_is_canonical`로 rename했고, assertion set도 `SUPPORTED_DECISION_CLASSES`로 바꿨습니다.
- 나머지 4개 test method와 `FIXTURE_HEADER`, `_parse_operator_request_header`, trailing `unittest.main()` block은 그대로 유지했습니다. test count도 5로 그대로입니다.
- `scripts/pipeline_runtime_gate.py`는 건드리지 않았고, blocking gate도 연결하지 않았습니다.
- stale `.pipeline/operator_request.md` (seq 462)는 이번 라운드에서 truth-sync하지 않았습니다. 해당 파일의 `REASON_CODE: advice_g5_not_bounded_first_sub_slice` drift는 별도 slice 후보(G7-live-file)로 남겨 두었습니다.
- `pipeline_gui/backend.py`와 `tests/test_pipeline_gui_backend.py`는 이번 라운드에서 수정하지 않았습니다. seq 504 G12 baseline은 그대로 유지했습니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474/477/480/483/486/489/495/498/501/504/507 shipped surfaces는 의도적으로 더 수정하지 않았습니다.
- doc-sync triage 결과 없음: 이번 변경은 operator-lane vocabulary symbol 추가와 test import 전환만 포함했고, README/spec/architecture surface를 새 계약으로 넓히지 않았습니다.

## 검증
- grep 확인
  - `rg -n 'SUPPORTED_DECISION_CLASSES' pipeline_runtime/operator_autonomy.py`
    - 결과: 1건 (`:53`)
  - `rg -n '"advisory_only"' pipeline_runtime/operator_autonomy.py`
    - 결과: 1건 (`:56`)
  - `rg -n 'SUPPORTED_DECISION_CLASSES' tests/test_operator_request_schema.py`
    - 결과: 2건 (`:5`, `:73`)
  - `rg -n 'OBSERVED_DECISION_CLASSES' tests/test_operator_request_schema.py`
    - 결과: 0건
  - `rg -n 'OBSERVED_DECISION_CLASSES' tests/`
    - 결과: 0건
  - `rg -n 'def test_decision_class_is_canonical' tests/test_operator_request_schema.py`
    - 결과: 1건 (`:70`)
  - `rg -n 'def test_decision_class_is_observed' tests/test_operator_request_schema.py`
    - 결과: 0건
  - `rg -n 'def test_' tests/test_operator_request_schema.py`
    - 결과: 5건 (`:36`, `:52`, `:61`, `:64`, `:70`)
  - `rg -n '@unittest.skip' tests/test_operator_request_schema.py`
    - 결과: 0건
  - `rg -n 'normalize_decision_class' pipeline_runtime/operator_autonomy.py`
    - 결과: 2건 (`:174` function definition, `:247` call site)
    - handoff 기대치는 function definition 1건이었지만, 현재 파일에는 `classify_operator_candidate` 내부 호출도 있어서 총 2건이 정상입니다. 구현상 함수 body는 unchanged입니다.
  - `rg -n '^SUPPORTED_' pipeline_runtime/operator_autonomy.py`
    - 결과: 3건 (`:47`, `:48`, `:53`)
  - `rg -n 'def _apply_supervisor_missing_status' pipeline_gui/backend.py`
    - 결과: 1건 (`:73`)
- canonical-set sanity check
  - `python3 -c "from pipeline_runtime.operator_autonomy import SUPPORTED_DECISION_CLASSES; assert len(SUPPORTED_DECISION_CLASSES) == 6; assert 'advisory_only' in SUPPORTED_DECISION_CLASSES; assert 'operator_only' in SUPPORTED_DECISION_CLASSES; print('OK')"`
    - 결과: `OK`
    - `len == 6`, `advisory_only in`, `operator_only in` 확인
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과: `Ran 5 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.098s`, `OK`
  - baseline confirmation: `45 / OK / skipped=0`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.024s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.075s`, `OK`
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.073s`, `OK`
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py tests/test_operator_request_schema.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- pipeline_runtime/operator_autonomy.py tests/test_operator_request_schema.py`
  - 결과: 출력 없음, 통과

## 남은 리스크
- `advisory_only`는 이제 CANONICAL이지만 implement 시점 기준으로는 repo 어디에도 OBSERVED되지 않았습니다. Gemini 509가 forward-looking literal로 포함시키는 결정을 내렸고, 이 사실은 이후 auditability를 위해 그대로 기록합니다.
- `normalize_decision_class`는 여전히 pass-through입니다. `DECISION_CLASS`의 runtime gating / canonical validation은 아직 강제되지 않으며, gate 또는 control-writer에 연결하는 것은 별도 slice(G7-gate-blocking)입니다.
- live `.pipeline/operator_request.md` (seq 462)는 여전히 non-canonical `REASON_CODE` literal을 가진 stale file입니다. advisory test를 live file parse로 넓히는 것은 별도 slice(G7-live-file)이며, 그 전에 drift-handling strategy가 필요합니다.
- G3 / G6-sub2 / G6-sub3 / G8-pin / G9 / G10 / G11은 계속 deferred입니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 이번 구현 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 0을 유지합니다.
- dirty worktree 파일은 두 target file 외에는 이번 라운드에서 건드리지 않았습니다.
