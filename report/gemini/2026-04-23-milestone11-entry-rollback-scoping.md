# 2026-04-23 Milestone 11 Entry: Rollback Scoping

## 요약
- Milestone 10 "Local Operator Operation"이 성공적으로 종료되고 문서화되었습니다.
- 다음 단계인 Milestone 11 "Operator Action Reversibility & Sandbox"의 첫 번째 구현 슬라이스로 **Rollback Restore 기능(Axis 1)** 구현을 권고합니다.
- 이는 Axis 2에서 확보한 백업 파일을 사용하여 대상 파일을 원본 상태로 복구하는 실질적인 가역성을 제공합니다.

## 권고 사항 (Milestone 11 Axis 1: rollback_local_file_edit_restore)

`local_file_edit` 작업에 의해 변경된 파일을 백업본으로 되돌리는 `rollback_operator_action` 함수를 구현합니다.

### 핵심 변경 내용
1. **Executor 확장**: `core/operator_executor.py`에 `rollback_operator_action(record: dict) -> dict` 함수를 추가합니다.
   - `record`에서 `backup_path`와 `target_id`를 읽습니다.
   - 백업 파일이 존재하면 이를 `target_id` 위치에 덮어씁니다.
   - 성공 여부와 결과를 반환합니다.
2. **단위 테스트 추가**: `tests/test_operator_executor.py`에 `test_local_file_edit_rollback_restores_content`를 추가하여 '쓰기 -> 백업 생성 -> 롤백 -> 원본 복구 확인'의 전체 사이클을 검증합니다.

### 테스트 전략
- `unittest`를 사용하여 임시 파일 환경에서 롤백 후 파일 내용이 정확히 원본과 일치하는지 확인합니다.

## 판단 근거
- **가역성 실현**: Milestone 10에서 백업이라는 "Ground Truth"를 확보했으므로, 이를 실제로 사용하여 상태를 복구하는 기능을 갖추는 것이 가역성(Reversibility) 보장의 완성입니다.
- **안전성 강화**: 실수로 잘못된 쓰기가 발생했을 때 시스템이 스스로 수습할 수 있는 능력을 갖추는 것은 향후 개인화 및 자동화 확장 이전에 필수적인 안전장치입니다.
