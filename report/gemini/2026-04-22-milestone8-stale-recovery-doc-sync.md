# 2026-04-22 Milestone 8 Axis 5 Complete - Stale Recovery

## Context
- Milestone 8 Axis 5 (Stabilization) 및 Milestone 7 Axis 4 (suggested_scope enum, seq 849) 구현이 이미 완료되어 커밋되었습니다 (SHA `50d110a`).
- `pipeline-launcher risk burn-down` 번들 역시 이미 커밋되었습니다 (SHA `09934be`).
- 현재 시스템이 `stale_control_seq=true` 상태인 이유는, 구현이 완료되었음에도 불구하고 `implement_handoff.md` (seq 849)와 `operator_request.md` (seq 848)가 최신 상태를 반영하지 못하고 정체되어 있기 때문입니다.

## Analysis
- **Milestone 8 Axis 1-5**: 전 패밀리 서비스 fixture 확보, Loader 구현 및 테스트, 패키지 export가 모두 완료되었습니다.
- **Milestone 7 Axis 4 (Enum)**: `CandidateReviewSuggestedScope` 정의 및 저장소 검증 로직이 seq 849를 통해 반영되었습니다.
- **Stale State**: 이미 커밋된 작업(seq 849)을 다시 수행하라는 handoff가 활성화되어 있어 자동화가 진행되지 않고 있습니다.

## Decision
- 현재의 정체 상태를 해소하기 위해, 이미 완료된 seq 849의 진척도를 문서에 동기화(Doc-Sync)하고 Milestone 8의 다음 단계인 "Family-specific trace extensions"로 축을 이동합니다.

## Recommendation
- **RECOMMEND: implement Milestone 8 Axis 6 (Doc-Sync for Axis 6 & Family Extensions)**
- **Doc-Sync**: `docs/MILESTONES.md`에 Axis 6 (CandidateReviewSuggestedScope enum)이 seq 849를 통해 shipped 되었음을 기록합니다.
- **Family-Specific Trace**: `core/eval_contracts.py`에 각 패밀리별 특화 필드(예: `CorrectionReuseTrace`의 `original_text`/`corrected_text`)를 포함하는 TypedDict 정의를 시작합니다.
- **Verification**: `tests/test_eval_loader.py`를 확장하여 패밀리별 확장 필드에 대한 검증 로직이 Loader에서 정상 작동하는지 확인합니다.

## Next Action
- `advisory_advice.md`를 통해 Axis 6 완료 기록 및 Axis 7(데이터 보강) 진입을 조언합니다.
