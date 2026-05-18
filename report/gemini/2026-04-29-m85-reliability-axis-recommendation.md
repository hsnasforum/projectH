# 2026-04-29 M85 Direction: Preference Reliability Axis (Option B)

## 개요
M79–M83을 통해 `Correction -> Preference -> Auto-Activate`로 이어지는 "관측 루프(Observability Loop)"의 골격이 완결되었습니다. 현재 사용자는 교정 패턴을 선호도로 승격시키고, 그 결과를 UI에서 즉시 확인할 수 있습니다. 하지만 승격된 선호도가 실제 모델의 응답에 즉각적으로 영향을 미치는 "신뢰도 전이" 단계에서 기능적 공백(Gap)이 발견되었습니다.

## 현황 분석 및 문제점
1. **신뢰도 지체 현원**: 현재 `is_highly_reliable_preference` 로직은 승격 후의 `applied_count >= 3` 조건을 필수적으로 요구합니다.
2. **프롬프트 주입 차단**: `AgentLoop`는 기본적으로 `highly_reliable_only=True` 필터를 사용하여 선호도를 주입합니다.
3. **결과**: 사용자가 빈번하게 발생하던 교정 패턴을 "승격"하여 `ACTIVE` 상태가 되었음에도 불구하고, 승격 직후에는 `applied_count`가 0이므로 실제 프롬프트 주입 대상에서 제외됩니다. 이는 "승격했으나 즉시 적용되지 않는" 사용자 경험의 불일치를 초래합니다.

## 권고: Option B (Reliability Axis)
M85의 첫 번째 슬라이스로 **Option B**를 추천합니다.

### 선택 이유
- **관측 루프의 실질적 완성**: 교정 단계의 "재발 횟수(Recurrence Count)"라는 관측 데이터를 승격 시점의 "초기 신뢰도(Initial Reliability)"로 변환하여, 승격 즉시 모델 행동에 반영될 수 있도록 합니다.
- **가치 중심적 접근**: 단순히 데이터를 쌓는 것(Option A)보다, 이미 쌓인 데이터를 신뢰도로 치환하여 사용자에게 실질적인 개인화 가치를 즉시 제공하는 것이 우선순위가 높습니다.
- **충돌 위험 관리**: 백엔드 로직(Axis 1) 중심으로 시작할 경우, 현재 PR #69에서 진행 중인 UI 작업과의 직접적인 충돌을 피하면서 구현을 병행할 수 있습니다.

### 구현 전략 (Axis 1)
- **Data Bridge**: `app/handlers/corrections.py`에서 승격 시점에 교정 저장소의 `recurrence_count`를 `PreferenceRecord` 생성 인자로 전달.
- **Reliability Logic**: `storage/preference_utils.py`의 `is_highly_reliable_preference`를 수정하여, `applied_count < 3`이더라도 높은 `initial_recurrence_count`를 가진 경우 신뢰할 수 있는 것으로 간주하는 "Fast-track" 경로 추가.
- **Contract Update**: `core/contracts.py`에 관련 필드 정의 추가.

## 대안 검토
- **Option A (Persistence)**: 성능 최적화 및 구조적 견고함을 위해 필요하지만, 현재 세션 수가 급증하여 `get_global_audit_summary`가 병목이 되는 단계는 아니므로 차순위로 미룰 수 있습니다.
- **Option D (Stability)**: M84에서 `stale_cancel_guard`를 통해 시급한 안정성 이슈를 일부 해소하였으므로, 현재는 기능적 가치 강화에 집중할 시점입니다.

## 추천
**RECOMMEND: implement M85 Axis 1 (Backend Reliability Logic for Promoted Preferences)**
- PR #62–#72 머지 대기 중에도 `storage/preference_utils.py` 및 `app/handlers/corrections.py` 백엔드 로직 수정을 통해 병행 구현 가능.
- UI 반영(Axis 2)은 PR #69 머지 후 진행 권고.
