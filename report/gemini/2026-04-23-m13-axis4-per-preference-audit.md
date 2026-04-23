# 2026-04-23 Milestone 13 Per-Preference Reliability Scoping

## 요약
- Milestone 13 Axis 3(유효성 지표 베이스라인) 완료 후, 글로벌 통계를 넘어 개별 선호도별 성능을 정밀 분석하는 **개별 선호도 신뢰도 분석(Axis 4)** 구현을 권고합니다.
- 현재 개인화 교정률은 전체 평균으로만 집계되므로, 특정 선호도가 응답 품질을 지속적으로 악화시키는지 아니면 개선하는지 식별할 수 없습니다.
- 이 슬라이스는 "개인화 자동 활성화"로 가기 위한 최후의 데이터 검증 단계입니다.

## 권고 사항 (Milestone 13 Axis 4: Per-Preference Reliability Analysis)

`applied_preference_ids` 데이터를 활용하여 각 선호도(Preference)별로 교정 유발 횟수와 성공 횟수를 집계하고 신뢰도 점수를 산출합니다.

### 핵심 변경 내용
1. **저장소 확장**: `SessionStore.get_global_audit_summary()`가 `per_preference_stats` 딕셔너리를 반환하도록 확장합니다.
   - 키: `preference_id`
   - 값: `{"applied_count": N, "corrected_count": M}`
2. **분석 로직**: 메시지 루프를 돌며 `applied_preference_ids` 리스트에 포함된 모든 ID에 대해 카운트를 누적합니다.
3. **Audit 보고서 보강**: `scripts/audit_traces.py`에서 개별 선호도별 교정률을 내림차순으로 출력하여 "문제 있는 선호도"를 한눈에 파악할 수 있게 합니다.

### 테스트 전략
- `tests/test_session_store.py`에 동일한 선호도가 여러 메시지에 적용되고 그 중 일부만 교정되었을 때, 개별 카운트가 정확히 합산되는지 확인하는 테스트를 추가합니다.

## 판단 근거
- **정밀 감사(Granular Audit)**: 프로젝트 가드레일(Priority #3)은 자동화 확장 전에 강력한 근거를 요구합니다. 글로벌 지표는 데이터가 많아질수록 문제를 가릴 수 있으나, 개별 지표는 즉각적인 위험 신호를 제공합니다.
- **자동화 임계값의 근거**: 특정 선호도가 10회 이상 적용되었음에도 교정률이 10% 미만이라면, 해당 선호도는 `cross_session_count`와 관계없이 "자동 활성화"의 강력한 후보가 됩니다.
- **안전한 다음 단계**: 실제 모델 레이어를 변경하지 않고 분석 도구만 확장하므로, PR #27 머지 전후 언제든 안전하게 수행할 수 있는 "bounded automatic slice"입니다.
