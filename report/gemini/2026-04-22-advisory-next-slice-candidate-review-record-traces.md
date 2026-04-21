# 2026-04-22 advisory-next-slice-candidate-review-record-traces

## 개요
- **REQUEST**: `advisory_milestone5_next_slice_after_durable_candidate_queue_items` (seq 731)
- **CONTEXT**: seq 729 `durable candidate queue items` 구현 및 검증 완료. `TASK_BACKLOG.md`의 `NextToAdd` 후보 중 다음 슬라이스 선정 필요.
- **DECISION**: **Item 6: Source-message candidate_review_record traces** 추천.

## 판단 근거
1. **데이터 자산 축적**: Milestone 5 및 7의 핵심 목표는 "검토되었으나 적용되지 않은(reviewed-but-not-applied)" 고품질 데이터 자산을 쌓는 것입니다. Item 6는 이 단계에서 필요한 마지막 데이터 필드인 `edit` 수용 능력을 확보하고, 감사(audit) 기록의 완결성을 높이는 슬라이스입니다.
2. **어휘 확장(Vocabulary Expansion)**: Milestone 7은 `accept`/`reject`/`defer` 외에 `edit` 어휘 확장을 지시하고 있습니다. 사용자가 소스 메시지의 교정 텍스트를 직접 수정하지 않고, 검토 단계에서 제안된 statement를 편집하여 수락할 수 있게 함으로써 "가르칠 수 있는 에이전트(teachable agent)"로의 진척을 이룹니다.
3. **후속 단계와의 정합성**: Item 7(reviewed scope selections)로 넘어가기 전, 검토 결과(특히 편집된 내용)가 소스 메시지 앵커에 정확하고 완결성 있게 기록되는 것이 선행되어야 합니다.

## 추천 슬라이스 상세 (Item 6)
- **목표**: `candidate_review_record` 어휘에 `edit` 추가 및 검토 감사 기록(trace)의 완결성 강화.
- **경계 및 제약**:
    - **입력**: 검토 큐에서의 `edit` 액션 및 수정된 statement 텍스트.
    - **출력**: `candidate_review_record`에 `review_action = edit`, `review_status = accepted_with_edits`, 그리고 `reviewed_statement` (편집된 텍스트) 기록.
    - **동작**: 기존 `TaskLogger`를 통해 `candidate_review_recorded` 이벤트 시 편집된 내용이 함께 로깅되도록 보강.
    - **제약**: 이 편집 내용은 아직 소스 메시지의 `corrected_text`를 덮어쓰거나 새로운 memory store로 이동하지 않음. 오직 "검토 기록"으로서만 존재.

## 남은 리스크
- **Dirty Worktree**: 누적된 미커밋 변경분(watcher 등)이 있으나, 이번 슬라이스는 `core/contracts.py`, `storage/session_store.py`, `app/handlers/aggregate.py`의 어휘 및 기록 로직에 한정되므로 안전하게 격리됩니다.
- **UI Interaction**: `edit` 액션은 API 레이어와 시리얼라이저 계약을 먼저 맞춘 뒤, 필요시 최소한의 UI 보강(편집 필드 노출 등)을 수반할 수 있습니다.
