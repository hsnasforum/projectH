# 2026-04-23 Milestone 10 Reversibility Backup

## 요약
- Milestone 10 Axis 1(`local_file_edit` 실제 쓰기)이 성공적으로 구현 및 검증되었습니다.
- Milestone 10의 목표인 "Observable and Reversible"을 달성하기 위해, 파일 덮어쓰기 전 원본을 보관하는 **백업 메커니즘(Axis 2)** 구현을 권고합니다.
- 이는 향후 롤백 기능을 위한 실질적인 "Ground Truth"를 확보하는 단계입니다.

## 권고 사항 (Milestone 10 Axis 2: Local File Edit Backup)

`local_file_edit` 액션 수행 시, `is_reversible: True` 설정이 있는 경우 기존 파일의 내용을 백업 디렉토리에 보관하도록 확장합니다.

### 핵심 변경 내용
1. **Executor 확장**: `core/operator_executor.py`에서 실제 쓰기(`Path.write_text`) 직전에 원본 파일이 존재하면 `backup/operator/` 아래에 타임스탬프가 포함된 이름으로 복사본을 생성합니다. 성공 시 `backup_path`를 결과 딕셔너리에 포함하여 반환합니다.
2. **계약 업데이트**: `core/contracts.py`의 `OperatorActionRecord` TypedDict에 `backup_path: str` 필드를 추가합니다.
3. **Agent Loop 연동**: `core/agent_loop.py`에서 `execute_operator_action`의 결과에 `backup_path`가 있으면 이를 `outcome_record`에 복사하여 세션 히스토리에 영속화되도록 합니다.

### 테스트 전략
- `tests/test_operator_executor.py`에 `is_reversible=True` 요청 시 실제 백업 파일이 생성되고 그 경로가 결과에 포함되는지 확인하는 테스트를 추가합니다.

## 판단 근거
- **가역성(Reversibility)**: 현재는 파일이 덮어써지면 복구가 불가능합니다. 백업은 롤백 기능을 위한 필수 선행 조건입니다.
- **감사 추적(Audit Trail)**: 백업 파일의 경력을 세션 히스토리에 남김으로써 시스템 변경 사항을 완벽하게 추적할 수 있게 됩니다.
