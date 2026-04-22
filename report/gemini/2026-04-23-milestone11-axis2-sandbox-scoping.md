# 2026-04-23 Milestone 11 Axis 2: Operator Sandbox Scoping

## 요약
- Milestone 11 Axis 1(Rollback Restore 기능)이 완료되었습니다.
- 다음 슬라이스로 시스템 안전성 보장을 위한 **경로 제한(Sandbox, Axis 2)** 구현을 권고합니다. (Option B)
- 실제 로컬 파일 쓰기가 활성화된 상태에서, 작업 대상이 프로젝트 루트를 벗어나지 못하도록 강제하는 것은 시스템 무결성 보호를 위한 필수 보안 조치입니다.

## 권고 사항 (Milestone 11 Axis 2: Path Restriction / Sandbox)

`local_file_edit` 및 롤백 작업의 `target_id`가 항상 프로젝트 루트(CWD) 하위 경로에 있도록 검증하는 로직을 추가합니다.

### 핵심 변경 내용
1. **검증 헬퍼 추가**: `core/operator_executor.py`에 `_validate_operator_action_target(target_id: str)` 함수를 구현합니다. (Option B)
   - `Path(target_id).resolve()`를 사용하여 절대 경로를 계산합니다.
   - `is_relative_to(Path.cwd().resolve())`를 사용하여 해당 경로가 현재 작업 디렉토리 하위에 있는지 확인합니다.
   - 위반 시 `ValueError(f"Path restricted: {target_id} is outside project root")`를 발생시킵니다.
2. **함수 적용**: `execute_operator_action`과 `rollback_operator_action`의 진입점에서 위 검증 헬퍼를 호출합니다.
3. **테스트 추가**: `tests/test_operator_executor.py`에 상위 디렉토리 참조(`../../etc/passwd`)나 루트 외부 절대 경로 요청 시 `ValueError`가 발생하는지 검증하는 테스트를 추가합니다.

### 차기 계획 (Axis 3: Rollback Trace)
- 롤백 이벤트 기록은 `agent_loop`에서 `rollback_operator_action` 호출 후 `record_operator_action_outcome`을 재사용하여 `status="rolled_back"`으로 기록할 것을 제안합니다.

## 판단 근거
- **보안 우선**: 쓰기 권한이 부여된 상황에서 "Sandbox"는 "Observable"보다 먼저 구현되어야 할 방어선입니다. 시스템 설정 파일이나 중요한 외부 파일에 대한 의도치 않은 수정을 방지하는 것이 최우선 과제입니다.
- **코드 재사용성**: 전용 검증 헬퍼를 도입함으로써 실행(execute)과 복구(rollback) 양측에 동일한 안전 기준을 일관되게 적용할 수 있습니다.
