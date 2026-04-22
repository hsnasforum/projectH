# 2026-04-22 Milestone 9 Entry

## 요약
- Milestone 8(평가 자산)이 Axis 1-8까지 모두 완료되어 committed 상태입니다.
- Milestone 9 "Approval-Gated Local Operator Foundation"의 전제 조건인 "안정적인 교정 및 선호도 메모리"와 "평가 기반"이 충족된 것으로 판단합니다.
- 다음 실행 슬라이스로 Milestone 9의 진입점인 `OperatorAction` 계약 정의를 권고합니다.

## 권고 사항 (Milestone 9 첫 슬라이스)

Milestone 9의 "one narrow operator surface"를 구체화하기 위해, 시스템이 수행할 수 있는 로컬 액션을 정의하고 이에 대한 승인·감사·롤백의 기반이 되는 계약을 수립합니다.

### 핵심 변경 내용
1. **OperatorActionKind (Enum)**: 로컬에서 수행될 액션의 종류를 정의합니다.
   - 예: `local_file_edit`, `shell_command_execute`, `session_state_mutation`.
2. **OperatorActionContract (TypedDict)**: 액션 수행 전 승인 단계에서 사용될 데이터 구조를 정의합니다.
   - 필드: `action_kind`, `target_id`, `requested_at`, `audit_trace_required: bool`, `is_reversible: bool`.
3. **contracts.py 확장**: `core/contracts.py`에 위 정의를 추가합니다.

### 테스트 전략
- `python3 -m py_compile core/contracts.py`를 통해 구문 오류가 없음을 확인합니다.
- 기존 Milestone 8 평가 엔진(`load_fixture`)이 새로운 계약 추가에 영향을 받지 않는지 회귀 확인합니다.

## 판단 근거
- **전제 조건 충족**: Milestone 6-8을 통해 메모리 루프와 평가 자산이 완성되었습니다. 이제 문서 작업(document work)을 넘어 액션(action)으로 확장할 수 있는 신뢰 기반이 마련되었습니다.
- **Narrow Entry**: 로컬 액션을 실제로 수행하기 전에, 무엇이 "Operator Action"인지 정의하는 것이 가장 좁고 안전한 시작점입니다. 이는 Milestone 9의 "define action approval, audit, and rollback expectations" 목표와 직접 연결됩니다.
