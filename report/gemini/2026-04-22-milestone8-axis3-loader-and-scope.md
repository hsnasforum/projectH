# 2026-04-22 Milestone 8 Axis 3 - Unit Helper (Fixture Loader)

## Context
- Milestone 8 Axis 2 (seq 831)가 완료되어 첫 번째 service fixture (`CORRECTION_REUSE`)와 `.gitignore` 예외 처리가 확보되었습니다.
- 현재 진척도는 `manual placeholder -> service fixture` 단계이며, 다음 목표는 `unit helper` 단계로 진입하여 fixture를 프로그램적으로 소비하는 것입니다.
- Milestone 7에서 미결된 `suggested_scope` enum 정의는 Milestone 8의 `SCOPE_SUGGESTION_SAFETY` fixture 설계와 연계되어야 합니다.

## Decision
- **Option B (Unit Helper — fixture loader)**를 다음 slice로 선정합니다.
- 단순 fixture 개수 확대(Option A)보다, fixture를 유효성 검증(Validation)하고 로드할 수 있는 인프라를 먼저 구축하는 것이 "Program operation follows stable memory" 원칙에 더 부합합니다.
- 이 과정에서 `SCOPE_SUGGESTION_SAFETY` fixture를 함께 추가하여 `suggested_scope` enum 값을 도출하고 Milestone 7의 공백을 닫습니다.

## Recommended Slice (Milestone 8 Axis 3)
1. **Fixture Loader (`eval/fixture_loader.py`)**: 
   - 신규 파일을 생성하고 `load_eval_fixture(path: Path) -> dict` 인터페이스를 구현합니다.
   - `core/eval_contracts.py`의 `EvalArtifactCoreTrace` 형상과 `EvalFixtureFamily` 및 `EVAL_FIXTURE_FAMILY_AXES` 매핑을 기준으로 유효성을 검사합니다.
2. **Safety Fixture**:
   - `data/eval/fixtures/scope_suggestion_safety_001.json`을 추가합니다.
   - 이 fixture 설계를 통해 `suggested_scope`에 허용될 값(예: `message_only`, `family_scoped`, `session_global`)을 확정합니다.
3. **Enum & Validation**:
   - `core/contracts.py`에 `CandidateReviewSuggestedScope(StrEnum)`를 정의합니다.
   - `storage/session_store.py`의 `_normalize_candidate_review_record`에서 해당 enum을 사용해 입력값을 검증하도록 수정합니다.

## Why Option B?
- **Stage Advancement**: "Service fixture"에서 "Unit helper"로 단계를 격상시켜 수동 작업의 정밀도를 도구(Tool)로 보장하기 위함입니다.
- **Contract Verification**: 첫 번째 fixture가 정의된 계약을 실제로 준수하는지 코드로 증명함으로써 향후 6개 패밀리 확대 시의 회귀 위험을 차단합니다.
