# 2026-04-22 Eval Family TypedDict Definitions

## 요약
- Milestone 8 "unit helper" 단계 완료 후, 각 `EvalFixtureFamily`에 특화된 `TypedDict` 필드 정의 요청.
- `core/eval_contracts.py`에 추가될 7개 가족별 확장 필드와 그 이유를 정의함.

## 권고 사항 (TypedDict 정의)

각 정의는 `EvalArtifactCoreTrace`를 상속하며 `total=False`를 유지합니다.

1. **CorrectionReuseTrace** (`correction_reuse`)
   - `reused_artifact_id`: `str` (필수 아님)
   - `reused_correction_id`: `str` (필수 아님)
   - **이유**: 특정 artifact 및 correction의 재사용 여부를 직접 연결하여 재사용 메커니즘의 유효성을 측정합니다.

2. **ApprovalFrictionTrace** (`approval_friction`)
   - `approval_latency_sec`: `float` (필수 아님)
   - `rejection_count`: `int` (필수 아님)
   - **이유**: 승인 과정에서의 지연 시간과 거절 횟수를 기록하여 사용자 마찰을 정량화합니다.

3. **ReviewabilityTrace** (`reviewed_vs_unreviewed_trace`)
   - `is_reviewed`: `bool` (필수 아님)
   - `review_action`: `str` (필수 아님, `CandidateReviewAction` 기반)
   - **이유**: 검토 여부와 수행된 구체적 액션을 기록하여 검토 상태가 품질에 미치는 영향을 비교합니다.

4. **ScopeSafetyTrace** (`scope_suggestion_safety`)
   - `suggested_scope`: `str` (필수 아님, `CandidateReviewSuggestedScope` 기반)
   - `safety_violation_count`: `int` (필수 아님)
   - **이유**: 제안된 스코어와 안전 위반 횟수를 짝지어 스코어 제안 엔진의 가드레일을 평가합니다.

5. **RollbackabilityTrace** (`rollback_stop_apply`)
   - `is_rollback_possible`: `bool` (필수 아님)
   - `rollback_target_artifact_id`: `str` (필수 아님)
   - **이유**: 롤백 가능 여부와 복구 대상을 기록하여 시스템의 가역성 및 정합성을 검증합니다.

6. **ConflictDeferTrace** (`conflict_defer_trace`)
   - `conflict_type`: `str` (필수 아님)
   - `deferral_count`: `int` (필수 아님)
   - **이유**: 충돌 유형과 보류(DEFER) 횟수를 추적하여 미결 정체 구간의 패턴을 식별합니다.

7. **ExplicitVsSaveSupportTrace** (`explicit_vs_save_support`)
   - `support_method`: `str` (필수 아님, "explicit", "implicit_save" 등)
   - `confidence_score`: `float` (필수 아님)
   - **이유**: 명시적 승인과 저장 기반 암묵적 지지를 대조하여 지지 신호의 신뢰도를 보정합니다.

## 제약 사항 준수 확인
- `CandidateReviewSuggestedScope` 값 재정의 안 함.
- `eval/fixture_loader.py` 로직 수정 권고 안 함.
- 모든 TypedDict `total=False` 유지.
- `core/contracts.py` 등 기존 코드의 필드 네이밍 규칙(count, action) 준수.
