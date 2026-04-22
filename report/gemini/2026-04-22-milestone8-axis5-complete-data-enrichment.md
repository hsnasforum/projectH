# 2026-04-22 Milestone 8 Axis 5 Complete - Eval Data Enrichment

## Context
- Milestone 8 Axis 5 (seq 843)가 완료되어 `tests/test_eval_loader.py`를 통한 검증 로직 안정화와 `eval` 패키지의 export 정리가 마무리되었습니다.
- 현재 7개 패밀리에 대한 기초 JSON fixture가 존재하지만, 내용은 최소 필드만 포함된 "placeholder" 수준입니다.
- `suggested_scope` enum 정의와 family-specific trace 확장 작업이 "Unit Helper" 단계의 마지막 과제로 남아 있습니다.

## Analysis
- 인프라(Loader, Contracts, Tests)가 안정되었으므로, 이제 "Workflow-Grade"라는 목표에 걸맞게 데이터를 구체화할 시점입니다.
- Milestone 7에서 파생된 `suggested_scope`의 값 제약을 확정하여 런타임 저장소(`session_store.py`)의 검증 루프를 완성해야 합니다.
- 각 패밀리(교정 재사용, 승인 마찰 등)의 특성을 반영한 세부 스키마(TypedDict)를 정의하고, 기존 fixture들을 실제 평가가 가능한 데이터로 보강(Enrichment)해야 합니다.

## Recommended Slice (Milestone 8 Axis 6)
1. **Enum & Validation**:
   - `core/contracts.py`에 `CandidateReviewSuggestedScope(StrEnum)`를 정의합니다. (허용 값: `message_only`, `family_scoped`, `global_preference`)
   - `storage/session_store.py`에서 `suggested_scope` 입력값이 이 enum에 속하는지 검증하는 로직을 활성화합니다.
2. **Family-Specific Schemas**:
   - `core/eval_contracts.py`에 `CorrectionReuseTrace`, `ApprovalFrictionTrace` 등 각 패밀리별 확장 필드를 포함하는 TypedDict를 정의합니다.
3. **Fixture Enrichment**:
   - `data/eval/fixtures/`의 7개 JSON 파일을 단순 placeholder에서 실제 시나리오를 담은 데이터(예: 교정 전/후 텍스트, 승인 지연 횟수 등)로 업데이트합니다.

## Next Action
- **RECOMMEND: implement Milestone 8 Axis 6 (Eval Data Enrichment)**
- 이 슬라이스를 통해 "Unit Helper" 단계를 완전히 졸업하고, 실제 세션 데이터를 평가 엔진에 주입하는 "E2E later" 단계로 넘어갈 모든 준비를 마칩니다.
