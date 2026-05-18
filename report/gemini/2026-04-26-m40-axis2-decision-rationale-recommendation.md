# 2026-04-26 M40 Axis 2 결정 사유(Rationale) 캡처 권고

## 상황 개요
- **M40 Axis 1 완료**: 리뷰 큐(Review Queue) 아이템에 원본 세션 정보(`source_session_id`, `source_session_title`)가 성공적으로 보강되었습니다.
- **차기 목표**: **Milestone 40 Axis 2: Decision rationale capture**를 통해 운영자가 리뷰 액션(수락, 거절, 보류)을 수행할 때 그 사유를 기록할 수 있게 합니다.
- **현상**: 백엔드 API(`submit_candidate_review`)와 세션 스토어(`record_candidate_review_for_message`)는 이미 `reason_note` 필드를 지원하고 있으나, 프런트엔드 UI에 입력 수단이 없으며 수락 시 생성되는 선호도 기록(Preference)에는 이 사유가 연동되지 않고 있습니다.

## 판단 근거
1. **의사결정 투명성**: "왜 이 교정 패턴을 수락/거절했는가"에 대한 사유는 나중에 선호도 기록을 감사하거나 조정할 때 중요한 근거가 됩니다.
2. **지식 자산화**: 단순한 패턴 매칭을 넘어 운영자의 의도가 기록된 사유는 향후 모델 튜닝이나 가이드라인 정립의 기초 자료가 됩니다.
3. **M40의 완결성**: Axis 1에서 "어디서(출처)"를 해결했으므로, Axis 2에서 "왜(사유)"를 해결하여 Milestone 40의 감사 가능성(Auditability) 목표를 달성합니다.

## 권고 사항 (RECOMMENDATION)
- **결정**: Milestone 40 Axis 2 구현을 시작합니다.
- **RECOMMEND: implement Milestone 40 Axis 2: Review Auditability — Decision Rationale Capture**
    - **Frontend**: `ReviewQueuePanel.tsx`에 사유(Rationale) 입력을 위한 textarea를 추가하고, `onReview` 및 `postCandidateReview` API 호출 시 이를 전달하도록 확장합니다.
    - **Backend**: `submit_candidate_review` (in `app/handlers/aggregate.py`)를 수정하여, 수락 시 `preference_store.record_reviewed_candidate_preference` 호출 시 `source_refs`에 `reason_note`를 포함하도록 합니다.
    - **Verification**: 사유가 포함된 리뷰 액션이 세션 메시지의 `candidate_review_record`와 생성된 `preference` 항목에 올바르게 저장되는지 확인합니다.

### 예상 결과
- 운영자가 리뷰 시 의도를 기록할 수 있어 선호도 학습 과정의 투명성 확보.
- 선호도 기록(Preference)에서 해당 규칙이 생성된 당시의 운영자 코멘트를 추적 가능.
