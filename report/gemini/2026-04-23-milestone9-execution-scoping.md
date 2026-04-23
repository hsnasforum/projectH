# 2026-04-23 Milestone 9 Execution Scoping

## 요약
- Milestone 9 Axis 2(스토리지 연동) 완료 후, 다음 슬라이스로 **최소 실행 스텁(Minimal Execution Stub)** 정의를 권고함.
- 이는 정의된 계약(`OperatorActionRecord`)을 기반으로 실제 로컬 액션이 안전하게 수행될 수 있는 "Narrow Operator Surface"의 첫 번째 실체를 만드는 단계임.

## 권고 사항 (Milestone 9 Axis 3: Minimal Execution Stub)

`LOCAL_FILE_EDIT` 액션에 대해 읽기 전용 프롭(Preview Probe) 기능을 수행하는 실행기를 구현합니다.

### 핵심 변경 내용
1. **Executor 모듈 생성**: `core/operator_executor.py` 파일을 생성하고 `execute_operator_action(record: OperatorActionRecord, store)` 함수를 정의함.
2. **LOCAL_FILE_EDIT 처리**: `target_id`로 전달된 경로의 파일을 읽어 내용의 일부(프리뷰)를 반환함. 실제 파일 수정은 하지 않음(Read-only).
3. **Agent Loop 연동**: `core/agent_loop.py`의 `_execute_pending_approval`에서 `OPERATOR_ACTION` 종류를 인지하고 위 실행기를 호출하도록 확장함.

### 테스트 전략
- **단위 테스트**: `OperatorActionRecord`를 executor에 전달했을 때 파일 내용을 올바르게 읽어오는지 확인.
- **통합 테스트**: `SAVE_NOTE`가 아닌 `OPERATOR_ACTION` 승인 시 에러가 아닌 "프리뷰 성공" 응답이 오는지 확인.

## 판단 근거
- **실체화**: 데이터 구조와 저장 방식이 준비되었으므로, 실제 액션이 시스템 내에서 어떻게 "동작"할지(단, 안전하게 읽기 전용으로) 정의하는 것이 가장 가시적인 진척임.
- **안전성**: `local_file_edit`의 첫 단계를 읽기 전용으로 제한함으로써 Milestone 9의 "observable" 가치를 확보하면서도 시스템 파괴 리스크를 최소화함.
