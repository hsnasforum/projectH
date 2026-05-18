# 2026-04-30 M117 다음 방향 권고 — advisory

## 요약
- **RECOMMEND: implement injection feedback loop (Candidate A)**
- **Exact slice**: `storage/session_store.py` 및 `storage/sqlite/session.py`의 `get_global_audit_summary()` 고도화 (`injected_count` 집계 추가)

## 현황 및 근거
M116을 통해 선호 주입의 관련성 품질(stop-word 필터링, 점수 기반 정렬)이 개선되었습니다. 이제 주입된 선호가 실제로 사용자에게 도달하고 영향을 미치는지 측정하는 '피드백 루프'의 완성이 필요합니다.

현재 `applied_count`는 최종 메시지에 저장된 `applied_preference_ids`만을 집계하므로, 주입 시도(`preference_injected`)는 되었으나 메시지 저장 실패나 세션 중단으로 인해 사용자에게 전달되지 않은 '유령 주입(Ghost Injections)'을 식별할 수 없습니다. 주입 시도 횟수(`injected_count`)를 지표에 포함함으로써, 주입-적용 전환율(Injection-to-Application rate)을 추적하고 모델의 지시 이행 품질을 평가할 기초 데이터를 확보할 수 있습니다.

## 권고 상세

### 1. 추천 방향: A) 주입 피드백 루프
- **이유**: 주입 품질(M116) 개선 이후 가장 중요한 것은 그 품질이 실제 지표로 증명되는지 확인하는 것입니다. `preference_injected` 이벤트를 신뢰도 통계에 반영하는 것은 'Teachable local personal agent'의 신뢰성 축(Reliability Axis)을 강화하는 필수 단계입니다.
- **D 후보(백로그 정리)**와의 관계: 백엔드 통계 로직 수정은 프론트엔드 PR 스택과 충돌 리스크가 매우 낮으므로, 백로그 정리를 기다리지 않고 병행하는 것이 효율적입니다.

### 2. 첫 번째 implement 슬라이스 scope
- **대상 파일**: `storage/session_store.py`, `storage/sqlite/session.py`
- **핵심 변경**:
    - `PerPreferenceStats` TypedDict: `injected_count` 필드 추가.
    - `get_global_audit_summary()`:
        - 세션별 `preference_injected` 태스크 로그 이벤트를 스캔하여 각 선호의 `injected_count`를 집계.
        - `applied_count`와 `injected_count`를 분리하여 제공함으로써, 주입 효율성을 시각화할 준비를 완료.
    - **핵심**: 주입되었으나 적용되지 않은 케이스를 통계적으로 노출.

## 리스크 및 중단 조건 (Stop Rule)
- 태스크 로그 전체 스캔으로 인해 `get_global_audit_summary`의 성능이 3초 이상으로 저하될 경우, 로그 스캔 방식을 최적화(예: 세션 데이터 내에 주입 이력을 요약 저장)하는 방향으로 피벗하십시오.
- SQLite 백엔드에서 `get_global_audit_summary`의 집계 결과가 JSON 백엔드와 불일치할 경우, 즉시 중단하고 parity를 재검증하십시오.
