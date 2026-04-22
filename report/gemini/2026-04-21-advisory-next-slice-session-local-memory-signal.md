# 2026-04-21 advisory-next-slice-session-local-memory-signal

## 개요
- **REQUEST**: `advisory_milestone5_next_slice_after_richer_labels` (seq 726)
- **CONTEXT**: seq 725 `richer reason labels` 구현 및 검증 완료. `TASK_BACKLOG.md`의 `NextToAdd` 후보 중 다음 슬라이스 선정 필요.
- **DECISION**: **Item 3: Read-only `session_local_memory_signal` projections** 추천.

## 판단 근거
1. **데이터 연속성**: seq 725에서 추가된 `reason_label`들(approval_reason_record, corrected_outcome 등)은 `session_local_memory_signal`의 핵심 입력값입니다. 지금 이 슬라이스를 구현함으로써 새로 확보된 고해상도 데이터를 즉시 "작업 요약(working summary)"으로 투영할 수 있습니다.
2. **아키텍처 정합성**: Item 3는 기존 trace를 소비하는 읽기 전용 프로젝션입니다. 새로운 사용자 입력 UI나 위험한 쓰기 경로를 도입하지 않으면서도, Milestone 5의 목표인 "구조화된 교정 메모리(structured correction memory)"로 가는 필수 징검다리 역할을 합니다.
3. **백로그 우선순위**: `TASK_BACKLOG.md`의 `Next To Add` 목록에서 원래 Item 3가 Item 4보다 앞에 위치해 있었습니다. 데이터 수집(Item 4)이 선행된 만큼, 이제 그것을 신호(Item 3)로 변환하는 것이 자연스러운 순서입니다.

## 추천 슬라이스 상세 (Item 3)
- **목표**: `artifact_id` + `source_message_id`를 키로 하는 읽기 전용 세션 프로젝션 구현.
- **범위 (TASK_BACKLOG 15–18 규약 준수)**:
    - **Axes**: 
        - 최신 교정 상태: `corrected_outcome` (outcome, reason_label), `content_reason_record` (label, note)
        - 최신 승인 마찰: `approval_reason_record` (reason_label)
        - 최신 저장 연계: `save_content_source`, `approval_id`, `saved_note_path`
    - **제약**:
        - 별도 저장소나 task-log replay 없이 현재 세션 상태에서만 유도.
        - Thin & Linkage-oriented: 본문 복사본 저장 금지, 선호도 추론 금지, Artifact 간 집계(cross-artifact) 금지.

## 남은 리스크
- **Dirty Worktree**: 이전 라운드부터 누적된 미커밋 변경분들이 존재하나, 이는 대형 번들 단위 커밋 정책(seq 696)에 따른 것으로 다음 구현 슬라이스 진행의 차단 요소가 아닙니다.
- **G6/E2E Verify**: 환경 제약(PermissionError) 및 라이브 런타임 검증 리스크는 상존하나, Item 3의 데이터 모델 및 프로젝션 로직 구현과는 격리된 영역입니다.
