# 2026-04-23 Milestone 9 Failure Audit Scoping

## 요약
- Milestone 9 Axis 4(결과 저장소) 완료 후, 감사 기록의 완전성을 위해 **실패 결과 기록(Failure Outcome Recording)** 슬라이스를 추가로 권고함 (Option B).
- 현재 성공한 액션만 `operator_action_history`에 남고 실패(ValueError) 경로는 흔적 없이 사라지므로, Milestone 9의 "observable" mandate를 완벽히 충족하기 위해 이 간극을 메워야 함.

## 권고 사항 (Milestone 9 Axis 5: Failure Outcome Audit)

`core/agent_loop.py`의 예외 처리 블록을 확장하여 실패한 액션에 대한 상태와 에러 메시지를 영속화합니다.

### 핵심 변경 내용
1. **Agent Loop 수정**: `core/agent_loop.py`의 `_execute_pending_approval` 내 `except ValueError as exc:` 블록에서 `record_operator_action_outcome`을 호출하도록 함.
2. **실패 레코드 구성**: `status="failed"`와 `error=str(exc)` 정보를 포함한 outcome record를 생성하여 저장소에 전달함.
3. **가역성 기반 강화**: 실패 기록을 남김으로써 "어떤 시도가 실패했는지"에 대한 감사 추적을 완료하고, 이후 Milestone 9를 종료(Close)함.

### 테스트 전략
- **단위 테스트**: 지원하지 않는 `action_kind`나 잘못된 `target_id`로 승인을 요청했을 때, `operator_action_history`에 `status="failed"` 레코드가 생성되는지 확인.
- **회귀 테스트**: 성공 경로(`status="executed"`)의 기존 기록 로직이 유지되는지 확인.

## 판단 근거
- **감사 완전성**: 실패한 액션이 기록되지 않으면 시스템이 무엇을 시도했고 왜 실패했는지 사후에 파악할 수 없음. Foundation 단계에서 실패 경로까지 관찰 가능하게 만드는 것이 Milestone 9의 진정한 마침표임.
- **최소 슬라이스**: `core/agent_loop.py` 단일 파일의 수 줄 수정만으로 "observable" 신뢰도를 크게 높일 수 있는 고효율 작업임.
