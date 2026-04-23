# 2026-04-23 Milestone 13 Personalization Effectiveness Metric Scoping

## 요약
- Milestone 13 Axis 1, 2를 통해 개인화 적용 이력(`applied_preference_ids`)을 세션 메시지와 교정 기록(`CorrectionStore`)에 연결하는 배관 작업이 완료되었습니다.
- 다음 단계로, 수집된 데이터를 바탕으로 개인화의 실질적인 효과를 정량화하는 **유효성 지표 베이스라인(Axis 3)** 구축을 권고합니다.
- 이는 "안전하고 측정 가능한(Safe and Measurable)" 개인화라는 프로젝트 가이드라인을 충속하며, 향후 자동 활성화(Auto-activation) 임계값을 결정하기 위한 객관적 근거를 제공합니다.

## 질문에 대한 답변

### a. 전제 조건(Preconditions) 충족 여부
- **충족됨.** `reviewed_memory` 라이프사이클과 `delta_fingerprint` 기반의 재현 키가 이미 Shipped 코드에 존재합니다. 기술적으로는 교차 세션 집계와 자동 승격이 가능한 상태입니다.
- 하지만 프로젝트 가이드라인(Priority #3)은 자동화 확장 전에 "측정 가능성"을 요구하고 있습니다.

### b. 자동 활성화(`cross_session_count >= 3`) 허용 여부
- **전략적 보류 권고.** 기술적으로는 가능하고 가드레일 조건(conflict visibility 이후)도 충족되었으나, 현재는 **수동 활성화된 선호도가 실제로 응답 품질을 개선하고 있는지**를 먼저 확인하는 것이 안전합니다.
- 따라서 명시적인 가드레일 해제(Override)보다는, 현재의 추적(Tracking) 인프라를 활용한 지표 산출을 우선합니다.

### c. M13 최적의 차기 구현 슬라이스
- **Milestone 13 Axis 3: Effectiveness Metric Baseline**
- **파일**: `storage/session_store.py`, `scripts/audit_traces.py`
- **구현**: 
  - `get_global_audit_summary()`가 `personalized_response_count`와 `personalized_correction_count`를 집계하도록 확장합니다.
  - `audit_traces.py`가 "개인화 교정률(Personalization Correction Rate)"을 보고하도록 수정합니다.

## 권고 사항 (Milestone 13 Axis 3: Effectiveness Metric Baseline)

### 핵심 변경 내용
1. **지표 산출**: `applied_preference_ids`가 포함된 응답 중 사용자가 `corrected_text`를 남긴 비율을 계산합니다.
2. **저장소 확장**: `SessionStore.get_global_audit_summary()`에서 위 두 수치를 카운트하는 로직을 추가합니다. (읽기 전용 확장)
3. **가시성 확보**: `scripts/audit_traces.py` 실행 시 "Personalized Response Count"와 "Subsequent Correction Rate"를 출력하여, 개인화가 품질을 떨어뜨리고 있지 않은지 감시합니다.

## 판단 근거
- **안전 루프 완성**: Axis 1, 2에서 마련한 추적 장치를 실제로 "사용"하여 시스템의 건강 상태를 확인하는 단계입니다.
- **데이터 기반 자동화**: 이 지표가 안정적으로 낮게(즉, 교정이 적게) 유지될 때, 비로소 `cross_session_count` 임계값을 낮추거나 자동 활성화를 도입할 수 있는 데이터 기반의 정당성이 확보됩니다.
