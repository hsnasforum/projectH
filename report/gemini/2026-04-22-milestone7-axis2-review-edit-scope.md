# 2026-04-22 Milestone 7 Axis 2 - Review Action EDIT Scope

## Context
- Milestone 7 Axis 1 (TypeScript cleanup)이 완료되어 `npx tsc --noEmit`이 clean 상태(0 errors)입니다.
- 다음 단계는 `CandidateReviewAction`에 `EDIT`를 추가하고, 검토 후보를 사용자가 직접 수정하여 수락할 수 있는 흐름을 여는 것입니다.
- Milestone 7의 원칙에 따라, `EDIT` 결과 역시 "reviewed-but-not-applied" 상태로 머물러야 하며, 실제 메모리 적용이나 사용자 레벨 저장소 확장은 차후 슬라이스로 미룹니다.

## Recommended Slice (Milestone 7 Axis 2)
1. **Vocabulary Expansion (Backend)**:
   - `core/contracts.py`의 `CandidateReviewAction`에 `EDIT = "edit"` 추가.
   - `CANDIDATE_REVIEW_ACTION_TO_STATUS` 맵에 `edit: "edited"` 추가.
2. **Frontend Edit UI (`app/static/app.js`)**:
   - `검토 후보` 카드에 `편집 후 수락` 버튼 추가 (기본 `data-testid="review-queue-edit"`).
   - 클릭 시 해당 카드의 statement 영역을 textarea로 전환하거나, `prompt()` 등을 사용해 수정된 텍스트를 입력받는 최소한의 UI 구현.
   - 수정된 텍스트를 `candidate_review_record.reason_note` 필드에 담아 기존 `POST /api/candidate-review`로 전송.
3. **Backend Persistence (`storage/session_store.py`)**:
   - 기존 `record_candidate_review_for_message`가 `ALLOWED_CANDIDATE_REVIEW_ACTION_TO_STATUS`를 사용하므로, contracts 변경만으로 자동 수용됨을 확인.

## Decision on TypeScript Cleanup
- **Cleanup Priority**: Axis 1에서 수행한 4건의 오류 정리는 매우 적절했습니다. 향후 Milestone 7/8 작업 중 발생하는 신규 타입 불일치는 "발견 즉시 해결" 원칙을 유지하며, 별도의 대규모 cleanup 라운드로 미루지 않을 것을 권고합니다.

## Next Action
- `RECOMMEND: implement Milestone 7 Axis 2 (Review Edit Action)`
- `CandidateReviewAction.EDIT` 추가 및 프론트엔드 편집 UI 배선을 진행합니다.
