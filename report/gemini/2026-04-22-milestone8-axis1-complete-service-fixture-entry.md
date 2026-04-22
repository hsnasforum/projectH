# 2026-04-22 Milestone 8 Axis 1 Complete - Service Fixture Rollout

## Context
- Milestone 8 Axis 1 (seq 826)이 완료되어 `core/eval_contracts.py`에 7개 fixture family와 6개 quality axis가 명문화되었습니다.
- `docs/MILESTONES.md`의 cleanup 작업(seq 823) 역시 완료되어 진척도가 정확히 동기화되었습니다.
- 이제 "manual placeholder" 단계를 넘어 실제 데이터를 수반하는 "service fixture" 단계로 진입할 준비가 되었습니다.

## Analysis
- `core/eval_contracts.py`는 향후 모든 workflow-grade evaluation의 기준점이 될 정적 계약을 성공적으로 정의했습니다.
- `EvalFixtureFamily.SCOPE_SUGGESTION_SAFETY` 가 정의됨에 따라, Milestone 7에서 미뤄둔 `suggested_scope`의 허용 값 제약을 정의할 수 있는 근거가 마련되었습니다.
- Rollout 단계(`MILESTONES:434`)에 따라 다음 목표는 실제 평가 데이터를 담을 JSON/YAML 기반의 service fixture 파일을 생성하고 이를 로드할 기초 helper를 작성하는 것입니다.

## Recommended Actions
- **Commit & Push**: Milestone 8 Axis 1 (seq 826) 및 관련 work notes를 커밋하고 푸시합니다.
- **Next Slice (Milestone 8 Axis 2)**: 
  - **Service Fixture Entry**: `data/eval/fixtures/` 디렉터리를 생성하고 `CORRECTION_REUSE` 또는 `APPROVAL_FRICTION` 패밀리에 대한 첫 번째 샘플 fixture (JSON) 파일을 추가합니다.
  - **Scope Constraints**: `core/contracts.py`에 `suggested_scope`에 대한 구체적인 `StrEnum` (예: `message_only`, `family_scoped`, `session_global`)을 추가하고 `storage/session_store.py`에서 이를 검증하도록 업데이트합니다.
  - **Eval Loader**: `eval/harness.py` 또는 `eval/scenarios.py`에서 이 fixture들을 로드할 수 있는 기초 loader 뼈대를 작성합니다.

## Next Implementation Priority
- Manual placeholder 계약을 실제 평가 데이터(service fixture)와 연결하여 " Mistake reduction"을 측정할 수 있는 실질적인 토대를 구축합니다.
