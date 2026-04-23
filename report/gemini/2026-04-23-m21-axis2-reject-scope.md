# Advisory Log: M21 Axis 2 - Durable Global Reject Persistence Scope

## 개요
- **일시**: 2026-04-23
- **요청**: M21 Axis 2 (Durable Global Reject Persistence)의 정확한 범위 및 구현 전략 정의
- **상태**: M18-M20을 통해 글로벌 후보(Global Candidate) 기능이 완성되었으나, 거절(Reject)된 글로벌 후보의 상태가 영구 저장되지 않아 앱 재시작 시 동일한 후보가 다시 나타나는 사용자 경험 저해 요소가 발견됨.

## 분석 및 판단
1.  **현상**: 글로벌 후보는 특정 세션 메시지에 종속되지 않으므로, 기존의 메시지 기반 리뷰 기록 방식으로는 거절 상태를 보존할 수 없음. 
2.  **해결 전략**: 글로벌 후보 거절 시, 해당 지문(Fingerprint)을 `PreferenceStore`에 `REJECTED` 상태의 레코드로 즉시 생성함.
3.  **동작 원리**: 
    - `serializers.py:_build_review_queue_items`는 이미 `PreferenceStore`에 존재하는 지문은 리뷰 큐에서 제외하도록 구현되어 있음 (상태 무관).
    - 따라서 거절된 정보를 선호 저장소에 기록하는 것만으로 자연스럽게 리뷰 큐 노이즈가 차단됨.
4.  **확장성**: `record_reviewed_candidate_preference` 메서드를 확장하여 초기 상태(`status`)를 지정할 수 있도록 함으로써, 향후 다양한 리뷰 액션에 유연하게 대응할 수 있도록 함.

## 권고 사항 (RECOMMEND)
**RECOMMEND: implement M21 Axis 2 (Durable Global Reject Persistence)**

1.  **Storage Layer (JSON/SQLite)**:
    - `record_reviewed_candidate_preference()` 메서드에 `status: str | None = None` 파라미터 추가.
    - 레코드 생성 시 `status`가 제공되면 기본값(`candidate`) 대신 이를 사용.
    - 레코드 갱신 시 `status`가 제공되면 기존 상태를 덮어씀.
2.  **Backend Handler**:
    - `app/handlers/aggregate.py:submit_candidate_review` 수정.
    - 글로벌 후보(`message_id == "global"`)에 대해 `review_action == CandidateReviewAction.REJECT`인 경우, `record_reviewed_candidate_preference(..., status=PreferenceStatus.REJECTED)`를 호출하도록 보강.
3.  **Validation**:
    - 글로벌 후보 거절 -> 페이지 새로고침 -> 해당 후보가 리뷰 큐에서 사라지고 선호 목록(거절 필터링된)에도 나타나지 않는지 Playwright smoke test로 검증.
    - SQLite/JSON 저장소에 `REJECTED` 레코드가 올바르게 생성되는지 단위 테스트 검증.

## 기대 효과
- 한 번 거절한 부적절한 개인화 규칙이 반복적으로 노출되는 문제 해결.
- 글로벌 학습 루프의 완결성과 사용자 제어 신뢰도 향상.
- Milestone 21의 "Maturity" 목표에 부합하는 품질 강화.
