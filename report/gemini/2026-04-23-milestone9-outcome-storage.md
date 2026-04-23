# 2026-04-23 Milestone 9 Outcome & Audit Storage

## 요약
- Milestone 9 Axis 3(최소 실행 스텁) 완료 후, 실행 결과의 영속적 기록을 위한 **결과 저장소(Outcome Storage)** 구현을 권고함.
- 현재 승인된 액션은 대기열에서 제거(pop)된 후 실행되지만, 그 결과가 세션에 남지 않아 "감사 가능성(observable)"과 "가역성(reversible)" 확보에 한계가 있음.

## 권고 사항 (Milestone 9 Axis 4: Outcome & Audit Storage)

실행된 Operator Action의 이력을 추적할 수 있도록 세션 데이터 구조를 확장하고 결과 기록 메서드를 추가합니다.

### 핵심 변경 내용
1. **세션 스키마 확장**: `storage/session_store.py`의 `_default_session`에 `operator_action_history` 리스트를 추가하여 실행 완료된 액션 레코드를 보관함.
2. **Outcome 기록 메서드**: `storage/session_store.py`에 `record_operator_action_outcome(session_id, record)`를 구현함. 이 메서드는 액션 상태를 `executed` 또는 `failed`로 업데이트하고 이력 리스트에 추가함.
3. **Agent Loop 연동**: `core/agent_loop.py`의 `_execute_pending_approval`에서 액션 실행 후 `record_operator_action_outcome`을 호출하여 결과를 영속화함.

### 테스트 전략
- **세션 저장소 테스트**: `tests/test_session_store.py`에서 액션 요청 -> 팝(pop) -> 결과 기록 후 `operator_action_history`에 올바른 레코드가 존재하는지 확인.
- **회귀 테스트**: 기존 `messages` 및 `pending_approvals` 정규화 과정에서 새로운 이력 필드가 유실되지 않는지 확인.

## 판단 근거
- **감사 추적(Audit Trail)**: Milestone 9의 핵심 목표인 "observable"을 달성하기 위해서는 액션의 시작(승인)뿐만 아니라 끝(결과)이 반드시 기록되어야 함.
- **가역성 기반 마련**: 나중에 "rollback" 기능을 구현할 때, 이력 저장소에 남은 `is_reversible` 플래그와 `outcome_id`가 복구 대상 식별의 근거가 됨.
