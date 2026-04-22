# 2026-04-22 advisory-next-slice-durable-candidate-queue

## 개요
- **REQUEST**: `advisory_milestone5_next_slice_after_session_local_memory_signal` (seq 728)
- **CONTEXT**: seq 727 `session-local memory signal` 구현 및 검증 완료. `TASK_BACKLOG.md`의 `NextToAdd` 후보 중 다음 슬라이스 선정 필요.
- **DECISION**: **Item 5: Reviewable durable-candidate queue items** 추천.

## 판단 근거
1. **기능적 완결성**: 최근 라운드에서 `candidate_confirmation_record`와 `durable_candidate`에 대한 기초 계약(Backlog 56-58)이 마련되었습니다. 현재 검토 큐(review queue) 메커니즘은 이미 배포되어 있으나, 명시적 확인(explicit confirmation)을 거친 항목들이 실제 큐에 "검토 후보"로 노출되어 사용자 액션(`accept`/`reject`/`defer`)을 유도하는 연결 고리가 필요합니다.
2. **마일스톤 정합성**: Milestone 7(Reviewable Durable Candidate Surface)의 첫 번째 슬라이스인 "eligible durable_candidate 레코드를 위한 로컬 보류 검토 큐 표면" 목표에 정확히 부합합니다.
3. **위험 관리**: Item 5는 기존에 검증된 검토 큐 UI와 `candidate_review_record` 추적 로직을 재사용합니다. 새로운 저장소나 복잡한 병합 로직 도입 없이, 명시적 확인 레코드를 기반으로 한 "읽기 전용 프로젝션"을 큐에 주입하는 형태이므로 경계가 명확하고 안전합니다.

## 추천 슬라이스 상세 (Item 5)
- **목표**: 명시적 확인(`candidate_confirmation_record`)이 있는 grounded-brief 소스 메시지로부터 유도된 `durable_candidate` 프로젝션을 세션의 `review_queue_items`에 포함시켜 노출.
- **경계 및 제약**:
    - **입력**: `candidate_confirmation_record`가 존재하는 소스 메시지.
    - **출력**: 기존 `review_queue_items` 리스트에 해당 항목을 `durable_candidate` 타입으로 주입.
    - **동작**: 사용자가 큐에서 `accept`/`reject`/`defer` 클릭 시, 해당 소스 메시지에 `candidate_review_record`를 기록하고 큐에서 제거 (기존 `session_local` 검토 로직과 동일한 저장 경로 사용).
    - **제약**: 아직 사용자 수준 메모리(user-level memory)나 복잡한 교정 메모리 저장소로 확장하지 않음. 오직 "검토됨(reviewed-but-not-applied)" 상태의 데이터 자산 축적에 집중.

## 남은 리스크
- **Dirty Worktree**: 누적된 미커밋 변경분(watcher, automation health 등)이 존재하나, 이번 슬라이스는 `app/serializers.py` 및 `storage/session_store.py`의 프로젝션 로직에 한정되므로 기능적으로 격리됩니다.
- **G6 Verify**: 환경 제약 리스크가 있으나, 이번 슬라이스의 단위 테스트 및 기존 큐 로직 회귀 테스트 통과 여부로 충분히 검증 가능합니다.
