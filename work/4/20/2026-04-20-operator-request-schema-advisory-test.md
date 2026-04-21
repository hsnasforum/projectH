# 2026-04-20 operator_request schema advisory test

## 변경 파일
- `tests/test_operator_request_schema.py`

## 사용 skill
- `finalize-lite`: 실제 실행한 검증, doc-sync 필요 여부, `/work` closeout readiness만 묶어 구현 라운드를 마감했습니다.

## 변경 이유
- `operator_request.md` header의 `REASON_CODE` / `OPERATOR_POLICY` / `DECISION_CLASS` vocabulary는 operator-lane contract에서 중요하지만, 이번 라운드에서는 production gate나 live `.pipeline/operator_request.md`를 건드리지 않고 advisory-mode로만 canonical fixture를 검증하는 가장 작은 reversible slice가 필요했습니다.
- Gemini advice 506은 `DECISION_CLASS` 후보에 `advisory_only`를 제안했지만, 실제 repo의 observed `DECISION_CLASS:` usage scan에는 `operator_only`, `next_slice_selection`, `internal_only`, `truth_sync_scope`, `red_test_family_scope_decision`만 확인되어, 이번 테스트는 handoff가 고정한 observed set을 기준으로 truthfully 작성해야 했습니다.

## 핵심 변경
- `tests/test_operator_request_schema.py`를 새로 추가했습니다. advisory-mode, self-contained fixture, 5 test methods만 담은 단일 test file이며 총 85줄입니다.
- `tests/test_operator_request_schema.py:4`에서 `SUPPORTED_REASON_CODES`와 `SUPPORTED_OPERATOR_POLICIES`를 `pipeline_runtime.operator_autonomy`에서 직접 import하도록 했습니다. canonical vocabulary를 test 안에 literal로 중복 선언하지 않았습니다.
- `tests/test_operator_request_schema.py:7-15`에는 `OBSERVED_DECISION_CLASSES = frozenset({"operator_only", "next_slice_selection", "internal_only", "truth_sync_scope", "red_test_family_scope_decision"})`를 module scope에 두고, `rg DECISION_CLASS:` scan을 source로 다시 확인하라는 한 줄 comment를 붙였습니다.
- `tests/test_operator_request_schema.py:17-28`에는 handoff가 고정한 advisory fixture `FIXTURE_HEADER`를 raw string으로 두었습니다. live `.pipeline/operator_request.md`를 읽지 않고, blank line과 body line까지 포함한 self-contained fixture만 검증합니다.
- `tests/test_operator_request_schema.py:31-39`에는 `_parse_operator_request_header(text: str) -> dict[str, str]`를 inline helper로 구현했습니다. 첫 blank line 전까지 `^([A-Z_]+):\s*(.*)$` 형식만 읽어 header dict를 만듭니다.
- `tests/test_operator_request_schema.py:42-80`의 `OperatorRequestHeaderSchemaTests`는 5개 test method만 가집니다.
  - expected 8개 header key parse 확인
  - `STATUS` / `CONTROL_SEQ`가 first 12 lines 안에 있는지 확인
  - `REASON_CODE`가 `SUPPORTED_REASON_CODES`에 속하는지 확인
  - `OPERATOR_POLICY`가 `SUPPORTED_OPERATOR_POLICIES`에 속하는지 확인
  - `DECISION_CLASS`가 `OBSERVED_DECISION_CLASSES`에 속하는지 확인
- Gemini advice 506의 `advisory_only`는 의도적으로 쓰지 않았습니다. `rg -n 'advisory_only' tests pipeline_runtime .pipeline/README.md .pipeline/operator_request.md`와 `rg -n 'DECISION_CLASS: advisory_only' .pipeline tests pipeline_runtime`가 모두 0건이라, observed/adopted schema surface에 없는 literal을 새 test canonical set에 넣지 않았습니다.
- `pipeline_runtime/operator_autonomy.py`는 수정하지 않았고, `SUPPORTED_DECISION_CLASSES` frozenset 도입은 별도 slice로 defer했습니다.
- `scripts/pipeline_runtime_gate.py`는 수정하지 않았고, 이번 라운드에서는 blocking gate도 연결하지 않았습니다.
- production `.pipeline/*.md` 파일은 수정하지 않았습니다.
- `pipeline_gui/backend.py`와 `tests/test_pipeline_gui_backend.py`는 수정하지 않았습니다. seq 504 G12 refactor baseline은 그대로 유지했습니다.

## 검증
- grep 확인
  - `rg -n '^from pipeline_runtime.operator_autonomy' tests/test_operator_request_schema.py`
    - 결과: 1건 (`:4`)
  - `rg -n 'SUPPORTED_REASON_CODES' tests/test_operator_request_schema.py`
    - 결과: 2건 (`:4`, `:69`)
  - `rg -n 'SUPPORTED_OPERATOR_POLICIES' tests/test_operator_request_schema.py`
    - 결과: 2건 (`:4`, `:74`)
  - `rg -n 'OBSERVED_DECISION_CLASSES' tests/test_operator_request_schema.py`
    - 결과: 2건 (`:7`, `:80`)
  - `rg -n '@unittest.skip' tests/test_operator_request_schema.py`
    - 결과: 0건
  - `rg -n 'def test_' tests/test_operator_request_schema.py`
    - 결과: 5건 (`:43`, `:59`, `:68`, `:71`, `:77`)
  - `rg -n 'advisory_only' tests/test_operator_request_schema.py`
    - 결과: 0건
  - `rg -n 'def _apply_supervisor_missing_status' pipeline_gui/backend.py`
    - 결과: 1건 (`:73`)
- 추가 truth check
  - `rg -n 'advisory_only' tests pipeline_runtime .pipeline/README.md .pipeline/operator_request.md`
    - 결과: 0건
  - `rg -n 'DECISION_CLASS: advisory_only' .pipeline tests pipeline_runtime`
    - 결과: 0건
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과: `Ran 5 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.116s`, `OK`
  - baseline confirmation: `45 / OK / skipped=0`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.026s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.083s`, `OK`
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.085s`, `OK`
- `python3 -m py_compile tests/test_operator_request_schema.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- tests/test_operator_request_schema.py`
  - 결과: 출력 없음, 통과
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474/477/480/483/486/489/495/498/501/504 shipped surfaces는 의도적으로 더 수정하지 않았습니다.

## 남은 리스크
- `OBSERVED_DECISION_CLASSES`는 test file 안에서 수동 유지됩니다. 이후 라운드가 새로운 `DECISION_CLASS` literal을 도입하면 이 test는 의도적으로 fail해서 drift를 드러내게 되고, 그때는 set을 다시 scan해 갱신하거나 별도 slice에서 `operator_autonomy.py`에 `SUPPORTED_DECISION_CLASSES`를 도입해야 합니다.
- advisory-mode only입니다. 이 test는 실제 `.pipeline/operator_request.md`를 읽지 않으므로, historical drift나 live file drift는 잡지 못합니다. live file parse까지 넓히는 것은 별도 slice 후보입니다.
- Gemini advice는 `advisory_only`를 `DECISION_CLASS` 후보로 제안했지만, 이번 handoff는 그것과 일부러 다르게 observed in-repo set을 사용했습니다. 이후 별도 slice에서 `advisory_only`를 공식 vocabulary로 채택할지, 아니면 현 observed set을 authoritative set으로 고정할지 정리할 필요가 있습니다.
- G3 / G6-sub2 / G6-sub3 / G8 / G9 / G10 / G11은 계속 deferred입니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 이번 구현 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 0을 유지합니다.
- dirty worktree 파일은 single new test file 외에는 건드리지 않았습니다.
