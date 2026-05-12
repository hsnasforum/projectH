# 2026-04-30 M119 다음 방향 권고 — advisory

## 요약
- **RECOMMEND: implement correction feedback → injection reliability loop (Candidate A)**
- **Exact slice**: `storage/session_store.py` 및 `storage/sqlite/session.py`의 `get_global_audit_summary()` 수정 (주입되었으나 미적용된 선호의 교정 피드백 연결) 및 `storage/preference_utils.py` 신뢰도 모델 갱신.

## 현황 및 근거
M114~M118을 통해 선호 주입의 품질과 가시성(injected_count)이 확보되었습니다. 이제 'Teachable' 에이전트의 핵심인 '학습 루프'를 닫을 때입니다.

현재 시스템은 모델이 선호를 실제 응답에 반영(Applied)했을 때만 교정 여부를 추적합니다. 하지만 모델이 주입된 선호를 **무시(Ignored)**했고 사용자가 이를 **수동으로 교정(Corrected)**한 경우, 이는 해당 선호의 '표현력 부족'이나 '모델 저항'을 나타내는 강력한 신뢰도 신호입니다. 이 루프를 닫음으로써 에이전트는 어떤 선호가 모델에게 '잘 먹히지 않는지'를 스스로 파악할 수 있게 됩니다.

## 권고 상세

### 1. 추천 방향: A) 교정 피드백 → 주입 신뢰도 루프
- **이유**: "Injection-to-Correction" 루프를 닫는 것은 로컬 개인화 에이전트가 사용자의 교정 행동으로부터 '주입 효율'을 배우게 만드는 결정적 단계입니다. 이는 단순한 통계 표시를 넘어, 선호도의 실질적인 효용성을 판단하는 기준이 됩니다.
- **기대 효과**: 모델이 무시하는 선호를 식별하여 사용자에게 '표현 개선'을 제안하거나, 신뢰도가 낮은 선호의 주입 우선순위를 자동으로 낮추는 기초 데이터를 확보합니다.

### 2. 첫 번째 implement 슬라이스 scope
- **대상 파일**: `storage/session_store.py`, `storage/sqlite/session.py`, `storage/preference_utils.py`
- **핵심 변경**:
    - **통계 로직**: `get_global_audit_summary()`에서 메시지에 교정이 발생했을 때, 해당 메시지에 **주입(Injected)**되었으나 **적용(Applied)**되지 않은 선호들의 `corrected_count`도 함께 증가시키는 로직 검토. (또는 별도의 `missed_correction_count` 도입)
    - **신뢰도 모델**: `is_highly_reliable_preference()`가 `applied_count` 대비 `corrected_count`뿐만 아니라, `injected_count` 대비 `applied_count`(채택률)도 고려하도록 공식 업데이트.
    - **경고**: 채택률이 현저히 낮은 선호에 대해 `is_degraded` 또는 `needs_rephrasing` 신호 생성.

## 리스크 및 중단 조건 (Stop Rule)
- 주입-교정 연결 로직이 너무 공격적일 경우(관련 없는 교정인데도 주입된 모든 선호를 깎아내림), '교정된 텍스트와 선호 내용의 유사도 매칭' 등 방어적 필터링을 추가해야 합니다.
- `main` 브랜치의 clean base 상태에서 기존 `applied_count` 정의를 훼손하지 않도록 주의하십시오. (Applied는 계속 '모델이 반영한 케이스'로 남겨야 함)
