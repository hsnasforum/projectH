# 2026-04-22 Milestone 9 Wiring Scoping

## 요약
- Milestone 9 Axis 1(데이터 계약 정의) 완료 후, 다음 슬라이스로 **스토리지 및 승인 라이프사이클 연결(Wiring)**을 권고함.
- 이는 정의된 계약(`OperatorActionContract`)을 실제 시스템의 승인 게이트웨이(`ApprovalKind`)에 편입시켜 실행 가능한 구조를 만드는 단계임.

## 권고 사항 (Milestone 9 Axis 2: Storage & Approval Integration)

"one narrow operator surface"를 구체화하기 위해, 로컬 액션 요청을 시스템의 공식 승인 대기열(`pending_approvals`)에 통합합니다.

### 핵심 변경 내용
1. **ApprovalKind 확장**: `core/contracts.py`의 `ApprovalKind` enum에 `OPERATOR_ACTION` 멤버를 추가함.
2. **OperatorActionRecord 정의**: `core/contracts.py`에 액션 실행 결과와 상태를 추적할 수 있는 `OperatorActionRecord` TypedDict를 정의함. (승인 전후의 감사 추적 보장)
3. **Storage 연동**: `storage/session_store.py`에 `record_operator_action_request` 메서드를 추가하여, `OperatorActionContract`를 승인 대기열에 기록할 수 있도록 함.

### 테스트 전략
- **단위 테스트**: `record_operator_action_request` 호출 시 `pending_approvals`에 올바른 `OperatorActionKind`와 데이터가 쌓이는지 확인.
- **회귀 테스트**: 기존 `SAVE_NOTE` 승인 요청 및 처리 로직에 영향이 없는지 `tests/test_smoke.py` 수준에서 확인.

## 판단 근거
- **연속성 보장**: Axis 1에서 정의한 계약이 실제 스토리지 레이어에서 어떻게 다뤄질지 결정하는 것이 가장 논리적인 다음 단계임.
- **게이트웨이 확보**: `ApprovalKind.OPERATOR_ACTION`을 추가함으로써, 향후 `core/agent_loop.py`에서 로컬 액션을 안전하게 가로채고 승인 요청을 보낼 수 있는 통로가 열림. 이는 Milestone 9의 "Approval-Gated" 핵심 가치를 충족함.
