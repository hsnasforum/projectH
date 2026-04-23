# 2026-04-22 Post-Milestone 8 Direction

## 요약
- Milestone 8의 7개 Axis가 모두 완료되고 커밋되었습니다.
- 다음 실행 슬라이스로 `eval/fixture_loader.py`에 가족별 `TypedDict` 타입 검증을 추가하는 **Option B**를 권고합니다.
- 이는 seq 853에서 정의한 TypedDict 계약을 실제 런타임 검증에 연결하여 Milestone 8의 기술적 부채를 해결하고 평가 데이터의 정합성을 보장하기 위함입니다.

## 권고 사항 (Option B: Fixture Loader Enhancement)

`eval/fixture_loader.py`의 `_validate()` 함수를 확장하여 `core/eval_contracts.py`의 `EVAL_FAMILY_TRACE_CLASS`를 활용하도록 합니다.

### 핵심 변경 내용
1. **가족별 필드 추출**: `EVAL_FAMILY_TRACE_CLASS`에서 해당 가족의 TypedDict를 가져와 `__annotations__`를 통해 허용된 필드 목록을 도출합니다.
2. **미등록 필드 검증**: fixture JSON에 TypedDict 정의에 없는 필드가 포함되어 있으면 `ValueError`를 발생시킵니다.
3. **타입 정합성 검증 (선택적)**: 기본적인 `isinstance` 체크를 통해 TypedDict에 명시된 타입(str, float, int, bool)과 일치하는지 확인합니다.

### 테스트 전략
`tests/test_eval_loader.py`에 다음 테스트 케이스를 추가합니다:
- `test_family_specific_fields_validation`: 올바른 가족별 필드를 가진 fixture가 통과하는지 확인.
- `test_unknown_family_field_raises`: TypedDict에 없는 임의의 필드가 포함된 경우 실패하는지 확인.
- `test_field_type_mismatch_raises`: 필드 값이 정의된 타입과 다를 경우(예: float 대신 str) 실패하는지 확인.

## 판단 근거
- **Option A (Milestone 9 entry)**: 현재 메모리 단계가 완료되어 진입은 가능하지만, "Workflow-Grade Eval Assets"의 마지막 고리인 타입 검증이 빠져 있는 상태입니다. 기반을 완벽히 다진 후 액션(operator foundation)으로 나아가는 것이 안전합니다.
- **Option B (Loader Enhancement)**: seq 853(TypedDict 정의)과 seq 858(JSON 데이터 보강) 사이의 간극을 메우는 필수적인 "Internal Cleanup"입니다. Gemini Mandate의 "Technical Integrity"와 "Engineering Standards"를 충족하는 방향입니다.
