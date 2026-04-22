# 2026-04-22 Milestone 8 Service Fixture Enrichment

## 요약
- Milestone 8 "Axis 6" (가족별 TypedDict 정의) 완료 후, 다음 실행 슬라이스로 서비스 피스처(JSON) 데이터 확장을 권고함.
- 현재 6개 공통 필드만 가진 7개 피스처를 seq 853에서 정의한 TypedDict 필드로 보강하여 "Workflow-Grade" 자산을 완성함.

## 권고 사항 (서비스 피스처 보강)

`data/eval/fixtures/` 아래의 7개 JSON 파일을 수정하여 가족별 특화 필드를 추가합니다.

1. **correction_reuse_001.json**
   - 추가: `"reused_artifact_id": "art_prior_001"`, `"reused_correction_id": "corr_prior_001"`
   - 이유: 재사용 원천을 명시하여 `CorrectionReuseTrace` 계약을 충족함.

2. **approval_friction_001.json**
   - 추가: `"approval_latency_sec": 45.5`, `"rejection_count": 1`
   - 이유: 사용자 마찰 측정 지표를 포함하여 `ApprovalFrictionTrace` 계약을 충족함.

3. **reviewed_vs_unreviewed_trace_001.json**
   - 추가: `"is_reviewed": true`, `"review_action": "accept"`
   - 이유: 검토 상태와 액션을 명시하여 `ReviewabilityTrace` 계약을 충족함.

4. **scope_suggestion_safety_001.json**
   - 추가: `"suggested_scope": "family_scoped"`, `"safety_violation_count": 0`
   - 이유: 제안된 스코프와 안전 위반 여부를 기록하여 `ScopeSafetyTrace` 계약을 충족함.

5. **rollback_stop_apply_001.json**
   - 추가: `"is_rollback_possible": true`, `"rollback_target_artifact_id": "art_prev_002"`
   - 이유: 가역성 검증 데이터를 포함하여 `RollbackabilityTrace` 계약을 충족함.

6. **conflict_defer_trace_001.json**
   - 추가: `"conflict_type": "divergent_fact"`, `"deferral_count": 2`
   - 이유: 충돌 유형과 보류 횟수를 기록하여 `ConflictDeferTrace` 계약을 충족함.

7. **explicit_vs_save_support_001.json**
   - 추가: `"support_method": "explicit"`, `"confidence_score": 0.95`
   - 이유: 지지 방식과 신뢰도를 명시하여 `ExplicitVsSaveSupportTrace` 계약을 충족함.

## 판단 근거
- **Option C (loader enhancement)**: 유용하지만, 실제 데이터(fixtures)가 먼저 보강되어야 검증 로직이 의미가 있음.
- **Option B (e2e stage)**: 데이터 보강 후 진행하는 것이 더 충실한 연동 테스트가 됨.
- **Option A (Milestone 9)**: Milestone 8의 자산(fixtures)을 "Workflow-Grade"로 마감하는 것이 안정적인 기반 확보에 유리함.
