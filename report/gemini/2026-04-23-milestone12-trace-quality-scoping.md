# 2026-04-23 Milestone 12 Trace Quality Scoping

## 요약
- Milestone 12 Axis 2(Export) 결과, 137개의 교정 쌍이 JSONL로 확보됨.
- 다음 슬라이스로 `core/delta_analysis.py`를 연동하여 데이터의 가치를 평가하고 정제하는 **Trace Quality Scoring & Refinement (Axis 3)**을 권고함.
- 이는 단순히 모든 교정을 모으는 단계를 넘어, 개인화 자산으로서의 가치가 높은 "고품질(High Quality)" 트레이스를 선별하는 과정임.

## 권고 사항 (Milestone 12 Axis 3: Trace Quality Scoring & Refinement)

확보된 137개 교정 쌍에 대해 유사도(Similarity) 분석을 수행하고, 개인화 모델 학습이나 평가에 적합한 데이터셋으로 정제합니다.

### 핵심 변경 내용
1. **델타 분석 연동**: `scripts/export_traces.py`가 `core/delta_analysis.py`의 `compute_correction_delta`를 사용하도록 수정함.
2. **품질 필터링**: `similarity_score`를 기준으로 너무 미세한 수정(예: > 0.98, 단순 오타)이나 너무 과격한 수정(예: < 0.20, 주제 변경/삭제)을 걸러내는 로직을 추가함.
3. **메타데이터 보강**: 내보내는 JSONL에 `similarity_score`, `change_types`, `is_high_quality` 플래그를 추가하여 개인화 엔진이 데이터를 가중치 있게 다룰 수 있게 함.
4. **결과물 분리**: 모든 데이터를 담은 파일과 고품질 데이터만 선별한 파일(`data/high_quality_traces.jsonl`)을 구분하여 생성함.

### 테스트 전략
- **단위 테스트**: `tests/test_export_utility.py`에서 다양한 텍스트 쌍에 대해 예상된 `similarity_score`와 필터링 결과(Pass/Fail)가 산출되는지 확인 함.
- **회귀 테스트**: 델타 분석 연동 후에도 기존 export 기능의 안정성이 유지되는지 확인함.

## 판단 근거
- **자산 정제(Asset Refinement)**: Milestone 12의 목표인 "promote high-quality traces"를 달성하기 위해서는 "품질"에 대한 정량적 기준이 필요함.
- **데이터 기반 의사결정**: 정제된 데이터셋의 통계(평균 유사도 등)는 향후 "Adaptive Model Layer" 도입의 타당성을 입증하는 강력한 근거 데이터가 됨.
- **기존 자산 활용**: 이미 구축된 `core/delta_analysis.py`를 재사용함으로써 구현 비용을 최소화하고 기술적 일관성을 유지할 수 있음.
