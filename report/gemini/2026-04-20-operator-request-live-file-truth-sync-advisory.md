# 2026-04-20 operator-request-live-file-truth-sync-advisory

## 상황 요약
- `G7-live-file (Option A)` (seq 513)를 통해 실제 `.pipeline/operator_request.md` 파일의 drift를 감지하고 리포트하는 기능이 구현되었습니다.
- 현재 `tests/test_operator_request_schema.py`는 `REASON_CODE: advice_g5_not_bounded_first_sub_slice` (seq 462)가 비표준임을 올바르게 감지하여 테스트를 skip하고 있습니다.
- `G5` 패밀리는 이미 seq 501에서 성공적으로 종료되었으므로, 해당 정지 사유는 명백히 stale한 상태입니다.

## 판단
- **G7-live-file (Option C)** 슬라이스를 권고합니다.
- **이유**: `GEMINI.md`의 "same-family current-risk reduction" 기준에 따라, 감지된 drift를 실제로 해결하여 시스템을 일관된 상태로 되돌리는 것이 중요합니다. 현재 skip 상태인 테스트를 green으로 전환함으로써 자동화 파이프라인의 신뢰도를 높일 수 있습니다.
- **우선순위**: `G7` 패밀리가 오늘 매우 높은 생산성을 보이고 있으며, 이 슬라이스를 통해 "Advisory" 단계의 마지막 고리를 닫고 안정적인 상태(Green tests)에서 다른 축으로 전환할 수 있습니다.

## 권고 세부사항 (G7-live-file Option C)
- **핵심 변경**:
  - `.pipeline/operator_request.md` 파일을 현재 상태에 맞는 canonical 헤더로 truth-sync(갱신)합니다.
  - **갱신 내용**:
    - `STATUS: needs_operator`
    - `CONTROL_SEQ: 514` (또는 현재 라운드의 seq)
    - `REASON_CODE: waiting_next_control` (canonical 코드)
    - `OPERATOR_POLICY: internal_only` (canonical 코드)
    - `DECISION_CLASS: next_slice_selection` (canonical 코드)
    - `DECISION_REQUIRED: confirm next implementation slice`
    - `BASED_ON_WORK: work/4/20/2026-04-20-operator-request-live-file-option-a.md`
    - `BASED_ON_VERIFY: verify/4/20/2026-04-20-operator-request-live-file-option-a-verification.md`
  - `tests/test_operator_request_schema.py`는 수정하지 않습니다. 파일 갱신 후 테스트가 자동으로 skip에서 green으로 전환되는지 확인합니다.

## 검증
- `python3 -m unittest tests.test_operator_request_schema`를 실행하여 6개 테스트가 모두 **OK (skipped=0)** 가 되는지 확인합니다.
- `tests.test_pipeline_gui_backend` (45/OK) 및 `tests.test_smoke` 회귀 테스트를 확인합니다.
- `.pipeline/operator_request.md` 헤더가 지시한 대로 정확히 갱신되었는지 확인합니다.
