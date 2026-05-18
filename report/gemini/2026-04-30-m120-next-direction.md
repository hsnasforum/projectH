# 2026-04-30 M120 다음 방향 권고 — advisory

## 요약
- **RECOMMEND: implement reliability filter refinement (Candidate A)**
- **Exact slice**: `storage/preference_utils.py`의 `is_highly_reliable_preference()` 고도화 (`injection_correction_rate` 임계값 반영)

## 현황 및 근거
M119를 통해 '주입 대비 교정 비율(Injection Correction Rate)'이라는 강력한 부정적 신호(Negative Signal)를 수집할 수 있게 되었습니다. 이는 모델이 해당 선호를 주입받았음에도 불구하고 사용자가 만족하지 못해 직접 교정한 빈도를 나타내며, 선호의 '실질적 유효성'을 판단하는 핵심 지표입니다.

현재 `is_highly_reliable_preference()`는 과거의 `applied_count`와 `corrected_count`만 고려하고 있어, 모델이 선호를 무시하거나(Ignored) 잘못 적용하여 발생하는 최신 교정 경향을 즉각 반영하지 못합니다. 이 루프를 닫아 '학습하는 로컬 개인화 에이전트(Teachable local personal agent)'의 지능을 한 단계 높여야 합니다.

## 권고 상세

### 1. 추천 방향: A) `injection_correction_rate`를 신뢰도 필터에 반영
- **이유**: 데이터 수집(M119)이 완료되었으므로, 이를 실제 에이전트의 판단 로직에 '반영'하는 것이 North Star에 가장 부합합니다. 저항률이 높은 선호를 자동으로 주입 대상에서 제외하거나 강등함으로써 응답 품질의 하향 평준화를 방지할 수 있습니다.
- **임계값 제안**: 초기값으로 `injection_correction_rate > 0.25` (주입 4회 중 1회 이상 교정 발생 시) 선호를 'Highly Reliable'에서 제외하는 보수적 접근을 권장합니다.

### 2. 첫 번째 implement 슬라이스 scope
- **대상 파일**: `storage/preference_utils.py`, `tests/test_preference_store.py`
- **핵심 변경**:
    - `is_highly_reliable_preference()`:
        - `injection_correction_rate` 가 일정 수준(예: 0.25) 이상이면 `is_highly_reliable`을 `False`로 판정하는 로직 추가.
        - `applied_count`가 부족하더라도 `injected_count` 기반의 강력한 부정적 신호가 있으면 조기에 신뢰도를 조정하도록 설계.
    - **테스트**:
        - 주입은 많이 되었으나 교정이 잦은 선호가 자동으로 `is_highly_reliable=False`가 되는 케이스 검증.
        - 기존 수동 활성화(`is_highly_reliable=True` 명시 저장) 선호와 통계 기반 선호 간의 우선순위 충돌 방지 확인.

## 리스크 및 중단 조건 (Stop Rule)
- `injected_count`가 너무 적은 상태(예: 1~2회)에서 우연한 교정으로 인해 선호가 너무 쉽게 강등되는 '과적합(Overfitting)' 리스크가 있습니다. 최소 주입 횟수(예: 3회 이상) 조건을 병행하십시오.
- UI(Candidate C)가 병행되지 않으면 사용자가 왜 특정 선호가 더 이상 주입되지 않는지 알기 어렵습니다. M120 Axis 2에서 UI 가시성 확보를 즉시 이어가십시오.
