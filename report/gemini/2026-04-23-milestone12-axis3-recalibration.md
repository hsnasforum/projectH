# 2026-04-23 Milestone 12 Axis 3 Threshold Recalibration

## 요약
- Milestone 12 Axis 3(품질 점수화) 결과, 실제 데이터의 `similarity_score`가 [0.067, 0.090] 구간에 밀집되어 있어 기존 임계값(0.20)으로는 고품질 트레이스가 0건으로 집계됨을 확인했습니다.
- 이는 `grounded-brief` 교정이 단순 오타 수정이 아닌 문서 수준의 재작성(Rewrite)이기 때문이며, 이에 맞춘 **임계값 재조정(Option A)**을 권고합니다.

## 질문에 대한 답변

### Q1 — Threshold recalibration
**선택**: **(a) Lower the lower bound to 0.05**
**이유**: 로컬 데이터 분석 결과, 유효한 문서 수준의 교정 쌍이 0.05~0.10 사이의 낮은 character-level similarity를 보입니다. 0.05로 하한선을 낮추는 것이 "문서 재작성"이라는 데이터 특성을 반영하면서도, 완전히 무관한 노이즈를 걸러낼 수 있는 가장 합리적인 기준입니다.

### Q2 — Milestone 12 status
**상태**: **Axis 3 종료 및 Axis 4 진입 필요**
**이유**: 137개의 트레이스가 확보되었지만, 이들이 실제 "개인화 자산(Personalization Assets)"으로 승격되어 활용되는 단계가 아직 구현되지 않았습니다. 품질 필터를 통과한 데이터셋이 비어 있지 않도록 조정한 후, 실제 승격 로직을 구현하는 것이 Milestone 12의 완결성을 위해 필요합니다.

## 권고 사항 (Milestone 12 Axis 4: Trace-to-Asset Promotion)

품질 필터를 통과한 트레이스를 시스템이 공식적으로 인식하는 "Personalization Assets"로 등록하고 관리하는 슬라이스를 구현합니다.

### 핵심 변경 내용
1. **임계값 수정**: `scripts/export_traces.py`의 `_is_high_quality` 하한선을 `0.05`로 변경합니다.
2. **Promotion 스크립트 추가**: `scripts/promote_assets.py`를 신규 생성하여 `data/high_quality_traces.jsonl`에 포함된 항목들을 `CorrectionStore`에서 `status=PROMOTED`로 전환하거나 전용 자산 인덱스에 추가합니다.
3. **메타데이터 연동**: `stream_trace_pairs`가 메시지의 피드백(Helpful/Unclear) 유무를 함께 반환하도록 확장하여, 피드백이 있는 트레이스에 가중치를 부여할 수 있게 합니다.

### 테스트 전략
- `tests/test_export_utility.py`에서 0.05 임계값 적용 시 예상된 수(137개)가 `high_quality_traces.jsonl`에 포함되는지 확인합니다.

## 결정 이유
데이터를 모으고 점수를 매기는 단계(Axis 1-3)를 넘어, 이를 실제 시스템 자산으로 전환(Promotion)하는 과정을 완료함으로써 Milestone 12의 "promote traces into assets" 목표를 실질적으로 달성하기 위함입니다.
