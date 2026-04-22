# 2026-04-23 Milestone 13 Preference Reliability Visibility Scoping

## 요약
- Milestone 13 Axis 4(개별 선호도 분석)를 통해 로컬에 축적된 교정 데이터를 기반으로 각 선호도별 성능 지표를 산출할 수 있게 되었습니다.
- 다음 단계로 이 지표를 사용자 인터페이스에 노출하는 **Preference Reliability Visibility (Axis 5)** 구현을 권고합니다.
- 이는 "자동 활성화"로 가기 전, 사용자가 데이터에 기반하여 직접 선호도를 관리할 수 있게 돕는 핵심적인 안전 장치이자 사용자 경험 개선 단계입니다.

## 질문에 대한 답변

### a. 전제 조건(Preconditions) 충족 여부
- **충족됨.** `delta_fingerprint` 기반의 재현 키가 확립되었고, `reviewed_memory` 라이프사이클이 Shipped 코드에 존재합니다. 기술적으로는 자동 승격과 집계가 가능한 상태입니다.

### b. 자동 활성화(`cross_session_count >= 3`) 허용 여부
- **전략적 보류.** 프로젝트 가이드라인(Priority #3)은 자동화 확장 전에 "가시성"과 "측정 가능성"을 요구합니다. 현재 인프라 수준의 측정은 완료되었으나, 이를 사용자에게 노출하여 신뢰를 확인하는 과정이 먼저 필요합니다.

### c. M13 최적의 차기 구현 슬라이스
- **Milestone 13 Axis 5: Preference Reliability Visibility in UI**
- **파일**: `app/handlers/preferences.py`, `app/frontend/src/components/PreferencePanel.tsx`
- **구현**: 
  - 백엔드에서 `per_preference_stats`를 선호도 목록에 병합하여 반환합니다.
  - 프런트엔드 선호도 패널에 적용 횟수와 교정률(신뢰도) 표시를 추가합니다.

## 권고 사항 (Milestone 13 Axis 5: Reliability Visibility)

### 핵심 변경 내용
1. **데이터 결합**: `app/handlers/preferences.py`의 `list_preferences_payload()`에서 `per_preference_stats`를 읽어 각 선호도 객체에 `reliability_stats` 필드로 추가함.
2. **UI 표시**: `PreferencePanel.tsx`의 각 선호도 카드에 적용 횟수(`applied_count`)와 성공률(`100% - correction_rate`)을 시각화함.
3. **위험 신호**: 교정률이 높은(예: 30% 이상) 선호도에 대해 경고 아이콘이나 색상 변화를 통해 사용자 주의를 환기함.

### 테스트 전략
- `tests/test_preference_store.py`에서 병합된 페이로드가 정확한 통계를 포함하는지 확인.
- 프런트엔드 수동 확인을 통해 신뢰도 배지가 올바르게 렌더링되는지 점검.

## 판단 근거
- **신뢰 기반 자동화**: 사용자가 지표를 보고 에이전트의 판단(선호도 적용)을 신뢰하기 시작할 때, 비로소 안전한 자동 활성화로 넘어갈 수 있는 심리적/데이터적 기반이 완성됩니다.
- **안전 루프 확장**: Milestone 12의 "measurable" 가치를 UI 레이어까지 확장하여 프로젝트의 일관성을 유지합니다.
