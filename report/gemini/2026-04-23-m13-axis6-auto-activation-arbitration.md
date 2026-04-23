# 2026-04-23 Milestone 13 Axis 6 (Auto-Activation) Scoping Arbitration

## 요약
- PR #30 병합 완료 후 Milestone 13의 본격적인 자동화 단계인 **Axis 6 (Auto-Activation Logic)**으로의 전환을 권고합니다.
- M12 Axis 3에서 파생된 `latest_verify` artifact 이슈는 인프라 관측성 부채이며, 제품 가치 실현 관점에서 M13 Axis 6를 우선순위로 둡니다.

## 질문에 대한 답변

### Q1: 우선순위 결정
- **Milestone 13 Axis 6 (Auto-Activation)**을 먼저 진행할 것을 권고합니다.
- **이유**: Milestone 12 Axis 6를 통해 "JUSTIFIED" 판정이 내려졌고, M13 Axis 1-5를 통해 이미 개인화의 영향도를 측정할 수 있는 "Safety Loop"가 구축되었습니다. `latest_verify` artifact 이슈는 런타임의 UI 표시 버그 성격이 강하며, 제품의 핵심 로직인 개인화 자동화 추진을 늦출 정도의 블로커는 아닙니다.

### Q2: M13 Axis 6 Scope (정의)
- **명칭**: Auto-Activation Logic & Signal Thresholds
- **내용**: `CANDIDATE -> ACTIVE auto-activation remains deferred` 가드레일을 해제하고, 실제 자동 활성화 로직을 구현합니다.
- **세부 로직**:
  - `storage/preference_store.py`: `promote_from_corrections()` 또는 관련 헬퍼에서 `cross_session_count >= 3` 도달 시 `self.activate_preference()`를 자동 호출.
  - (선택 사항) Axis 4/5에서 구축된 신뢰도 지표(`correction_rate < 10%` 등)를 조건에 결합하여 안전성 강화.

### Q3: Implement Handoff 제안
- **슬라이스**: Milestone 13 Axis 6: Threshold-based Auto-Activation
- **대상 파일**:
  - `storage/preference_store.py` (로직 추가)
  - `tests/test_preference_store.py` (다중 세션 테스트 케이스 추가)
  - `docs/MILESTONES.md` (Axis 6 Shipped 기록 및 가드레일 업데이트)
- **완료 조건**:
  - 특정 선호도 지표가 임계값(count=3)을 넘었을 때 `status`가 `active`로 자동 전환됨.
  - 활성화된 선호도가 이후 세션의 프롬프트에 정상적으로 주입됨(기존 M13 Axis 1 로직 확인).
- **검증 방법**:
  - `pytest tests/test_preference_store.py`
  - `CorrectionStore.promote_correction` 호출을 모의한 시나리오 테스트.

## 판단 근거
- **Personalization Realization**: 이미 137개의 교정 자산과 23개의 후보가 확보된 상태에서 자동 활성화 로직만 연결되면 즉시 제품의 체감 성능이 개선됩니다.
- **Safety Loop Readiness**: Axis 1-5가 완료되어 자동 활성화 이후의 부작용을 즉시 감지하고 측정할 수 있는 상태입니다.
- **Deferred Debt Management**: `latest_verify` artifact 이슈는 M13 Axis 6 구현 과정에서 런타임 이벤트를 함께 점검할 때 companion fix로 고려하거나, 다음 인프라 정리 라운드로 넘기는 것이 효율적입니다.
