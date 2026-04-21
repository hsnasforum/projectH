# 2026-04-20 operator-request-vocabulary-g7-advisory

## 상황 요약
- `G12` 리팩토링(seq 504)이 성공적으로 완료되어 `pipeline_gui/backend.py`의 상태 전이 로직이 공통 헬퍼로 정리되었습니다.
- 이제 `pipeline_gui` 런타임 영역의 시급한 내부 정리는 일단락된 것으로 보입니다.
- 다음 슬라이스 후보 중 `G7`은 3-agent 자동화 파이프라인의 핵심인 `operator_request.md` 헤더의 메타데이터(REASON_CODE, OPERATOR_POLICY, DECISION_CLASS) 어휘(vocabulary)를 표준화하고 이를 검증하는 테스트를 도입하는 안입니다.

## 판단
- **G7: Canonical REASON_CODE / OPERATOR_POLICY / DECISION_CLASS vocabulary enforcement (advisory-mode first)** 슬라이스를 권고합니다.
- **이유**: 현재 `operator_request.md`에서 사용되는 메타데이터 어휘가 `pipeline_runtime/operator_autonomy.py`에 정의된 정규 세트와 괴리되는 경우가 발생하고 있습니다(예: seq 462의 `red_test_family_scope_decision`). 이는 런타임 분류기가 정지 사유를 오판하거나 불필요한 publish를 유발하는 리스크가 됩니다.
- **우선순위**: `GEMINI.md`의 "same-family current-risk reduction" 기준에 따라, 자동화 파이프라인의 안정성을 높이는 이 슬라이스가 현재 가장 타당합니다.

## 권고 세부사항 (G7)
- **대상 파일**: `tests/test_operator_request_schema.py` (신규 테스트 파일)
- **핵심 변경**:
  - `pipeline_runtime/operator_autonomy.py`에 정의된 `SUPPORTED_REASON_CODES` 및 `SUPPORTED_OPERATOR_POLICIES`를 참조하여, 대표적인 `operator_request.md` 헤더 픽스처(문자열)를 파싱하고 유효성을 검사하는 유닛 테스트 추가.
  - `DECISION_CLASS`의 유효 세트(예: `operator_only`, `advisory_only`, `red_test_family_scope_decision` 등)를 정의하고 이를 함께 검증.
  - 이번 슬라이스는 실제 `.pipeline/operator_request.md` 파일을 검사하거나 런타임 게이트 동작을 바꾸지 않는 "Advisory-mode"로 한정합니다.
- **검증**:
  - 신규 유닛 테스트가 green을 유지하는지 확인.
  - `tests.test_smoke` 및 `tests.test_pipeline_gui_backend` regression pass 확인.

## 대안 검토
- **G8-pin (Memory-foundation)**: 장기적인 방향성에는 부합하나, 현재 파이프라인의 구조적 신뢰도를 먼저 높이는 G7이 risk reduction 측면에서 우선합니다.
- **G3 (Reinvestigation tuning)**: 구체적인 incident trace 없이 수치를 조정하는 것은 투기적(speculative)이므로 뒤로 미룹니다.
