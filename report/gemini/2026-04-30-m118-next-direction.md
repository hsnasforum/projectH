# 2026-04-30 M118 다음 방향 권고 — advisory

## 요약
- **RECOMMEND: implement `injected_count` API exposure and UI display (Candidate A)**
- **Exact slice**:
    - `storage/session_store.py` & `storage/sqlite/session.py`: `_increment_preference_injection_count` 버그 수정 (미적용 선호도 집계 누락 방지).
    - `storage/preference_utils.py`: `_normalized_reliability_stats()`에 `injected_count` 지원 추가.
    - `app/frontend/src/api/client.ts`: `PreferenceRecord` 타입 갱신.
    - `app/frontend/src/components/PreferencePanel.tsx`: 주입 횟수 및 주입 대비 적용 비율(Conversion Rate) UI 표시.

## 현황 및 근거
M117을 통해 백엔드에서 `injected_count` 집계 기반이 마련되었으나, 현재 API와 UI에는 노출되지 않아 사용자가 선호 주입의 실질적인 동작 여부를 확인할 수 없습니다.

특히 코드 분석 결과, 현재 `get_global_audit_summary()`는 메시지에 한 번이라도 적용된 적이 있는 선호에 대해서만 주입 횟수를 합산하는 논리적 결함이 발견되었습니다. 주입은 되었으나 모델이 무시하여 적용되지 않은 '0% 전환율' 선호를 식별하는 것이 주입 품질 개선의 핵심이므로, 이 버그 수정과 함께 UI 가시성을 확보하는 것이 M118의 최우선 과제입니다.

## 권고 상세

### 1. 추천 방향: A) `injected_count` API 노출 및 UI 표시
- **이유**: 관찰 가능성(Observability)은 개선의 전제 조건입니다. 사용자가 "내 선호가 얼마나 자주 주입되고 모델에 의해 채택되는지"를 시각적으로 확인하게 함으로써, 'Teachable local personal agent'로서의 신뢰도를 높일 수 있습니다.
- **버그 수정 포함**: `_increment_preference_injection_count`에서 `summary["per_preference_stats"].get(preference_id)` 대신 `setdefault`를 사용하여, 적용된 적 없는 선호의 주입 횟수도 정확히 집계하도록 수정해야 합니다.

### 2. 첫 번째 implement 슬라이스 scope
- **대상 파일**: `storage/session_store.py`, `storage/sqlite/session.py`, `storage/preference_utils.py`, `app/frontend/src/api/client.ts`, `app/frontend/src/components/PreferencePanel.tsx`
- **핵심 변경**:
    - **Backend**: `injected_count` 집계 버그 수정 및 API 스키마 정규화 반영.
    - **Frontend**: `PreferencePanel`의 선호도 카드에 "주입 {N}회 (적용률 {M}%)" 형태의 텍스트 추가.
    - **지표**: `applied_count / injected_count` 비율을 통해 주입 효율성 시각화.

## 리스크 및 중단 조건 (Stop Rule)
- 전환율 계산 시 `injected_count`가 0인 경우 Zero-division 에러 처리가 누락되지 않도록 주의하십시오.
- `PreferencePanel` UI 레이아웃이 주입 횟수 표시로 인해 심하게 깨질 경우, 툴팁(Tooltip) 형식으로 대체하거나 요약 레이아웃을 재조정하십시오.
