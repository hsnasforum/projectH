# 2026-04-23 Milestone 12 Axis 4: Trace-to-Asset Promotion Scoping

## 요약
- Milestone 12 Axis 3(임계값 재조정) 결과, 137개의 고품질 트레이스가 확보되었습니다.
- 다음 슬라이스로 확보된 트레이스를 공식적인 개인화 자산으로 승격시키는 **Trace-to-Asset Promotion (Axis 4)**을 권고합니다.
- 이는 단순한 로그 파일(`jsonl`)을 넘어, 시스템이 관리하는 `CorrectionStore`의 상태를 갱신하여 향후 개인화 모델 레이어의 직접적인 입력으로 활용될 수 있게 하는 단계입니다.

## 권고 사항 (Milestone 12 Axis 4: Trace-to-Asset Promotion)

고품질 트레이스 데이터셋(`high_quality_traces.jsonl`)에 포함된 항목들을 `CorrectionStore`에서 `PROMOTED` 상태로 전환하고, 피드백 메타데이터를 통합합니다.

### 핵심 변경 내용
1. **SessionStore 확장**: `storage/session_store.py`의 `stream_trace_pairs()`가 메시지의 `feedback` 정보도 함께 반환하도록 수정합니다.
2. **Export 유틸리티 보강**: `scripts/export_traces.py`가 내보내는 JSONL에 `feedback` 필드를 포함하도록 업데이트합니다.
3. **Promotion 스크립트 생성**: `scripts/promote_assets.py`를 신규 생성합니다.
   - `data/high_quality_traces.jsonl`을 읽습니다.
   - `session_id`와 `message_id`를 매칭 조건으로 하여 `CorrectionStore`에서 해당 레코드를 찾습니다.
   - 찾은 레코드의 `promote_correction()` 메서드를 호출하여 상태를 `promoted`로 변경합니다.
4. **결과 검증**: 승격 완료 후 `CorrectionStore`의 통계(예: `PROMOTED` 상태인 레코드 수)를 출력합니다.

### 테스트 전략
- **단위 테스트**: `tests/test_export_utility.py`를 확장하여 피드백 정보가 포함된 트레이스가 올바르게 yield되는지 확인합니다.
- **통합 테스트**: `scripts/promote_assets.py` 실행 후 실제 `data/corrections/` 아래의 JSON 파일에서 `status` 필드가 `promoted`로 변경되었는지 확인합니다.

## 판단 근거
- **자산화의 완성**: 데이터를 정제하고 점수를 매기는 것(Axis 1-3)은 준비 단계이며, 이를 실제 시스템 자산(`CorrectionStore`)에 반영하는 것이 Milestone 12의 첫 번째 실질적인 "Promotion" 목표 달성입니다.
- **데이터 무결성**: 피드백 신호를 포함함으로써, 단순한 유사도 점수뿐만 아니라 사용자의 명시적 선호도가 반영된 고신뢰도 자산을 선별할 수 있게 됩니다.
- **자동화 기반**: 이 유틸리티들은 향후 모델 레이어가 주기적으로 자산을 수집하고 학습 데이터셋을 구성할 때의 핵심 툴 체인이 됩니다.
