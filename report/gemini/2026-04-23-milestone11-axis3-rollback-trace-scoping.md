# 2026-04-23 Milestone 11 Axis 3: Rollback Trace Scoping

## 요약
- Milestone 11 Axis 2(경로 제한 Sandbox)가 완료되었습니다.
- 다음 슬라이스로 **롤백 추적 기록(Rollback Trace, Axis 3)** 구현을 권고합니다.
- 이는 롤백 작업의 결과를 세션 히스토리에 영속화하여 시스템의 가역성을 사용자가 검증하고 감사할 수 있게 만드는 단계입니다.

## 권고 사항 (Milestone 11 Axis 3: Rollback Audit Trace)

`rollback_operator_action`의 결과를 `operator_action_history`에 기록하는 배관 작업을 수행합니다.

### 핵심 변경 내용
1. **상태값 추가**: 롤백 완료를 나타내는 `status="rolled_back"` 상태를 사용합니다.
2. **SessionStore 연동**: `storage/session_store.py`의 `record_operator_action_outcome` 메서드를 재사용하거나, 필요시 롤백 전용 메타데이터를 포함하도록 확장합니다. (현재 구현상 `outcome.setdefault("status", "executed")`이므로 호출 시 `status="rolled_back"`을 명시적으로 전달하면 재사용 가능)
3. **Agent Loop 확장**: `core/agent_loop.py`에 롤백을 처리할 내부 메서드(예: `_execute_operator_rollback`)를 준비하고, 실행 성공 시 `record_operator_action_outcome`을 호출하여 히스토리에 남깁니다.
4. **UserRequest 확장**: `UserRequest` 클래스에 `rollback_approval_id: str | None` 필드를 추가하여 미래의 UI 트리거를 위한 계약을 마련합니다.

### 테스트 전략
- `tests/test_operator_audit.py`에 롤백 수행 후 `operator_action_history`에 `rolled_back` 상태의 레코드가 정확히 추가되는지 검증하는 시나리오를 추가합니다.

## 판단 근거
- **관찰 가능성(Observable)**: "Observable and Reversible" Mandate에 따라, 복구 동작 역시 기록되어야 합니다. 기록되지 않은 복구는 시스템 상태에 대한 불확실성을 초래합니다.
- **아키텍처 일관성**: 실행 결과(`executed`, `failed`)와 동일한 히스토리 리스트에 `rolled_back` 이벤트를 쌓음으로써 단일 감사 로그(Audit Log)를 유지할 수 있습니다.
