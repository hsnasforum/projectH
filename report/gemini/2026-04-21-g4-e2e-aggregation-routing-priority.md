# 2026-04-21 AXIS-G4 e2e aggregation 및 순차 게이트 오분류 arbitration

## 개요
AXIS-G4 e2e 라이브 런타임 검증 결과, wrapper-events 발행은 확인되었으나 supervisor `events.jsonl` 집계 누락이 확인되었습니다. 또한, 연계된 순차 승인 게이트(B/C/D)가 선택지형 stop으로 오분류되는 false-positive 리스크가 식별되어 이에 대한 우선순위와 방향을 결정합니다.

## 판단 근거

### Q1. AXIS-G4 e2e — supervisor events.jsonl 집계 gap
- **결정**: (b) 코드 버그 (aggregation 경로 fix 필요)
- **이유**: ADR-008 및 관련 기술설계서는 `events.jsonl`을 런타임의 단일 authority path로 정의합니다. wrapper-events(DISPATCH_SEEN/TASK_ACCEPTED)가 이 파일에 집계되지 않는 것은 감사(audit) 및 thin client 연동 관점에서 기능적 결손(gap)이며, G4 e2e의 완전성을 위해 수정이 필요합니다.

### Q2. 순서 결정
- **권고 순서**: A (Marker fix) → C (Aggregation fix) → B (Branch commit)
- **이유**:
    1. **A**: `_MENU_CHOICE_BLOCKER_MARKERS` false-positive는 내일(`2026-04-22`) suppress window가 만료되는 즉각적인 라우팅 리스크입니다. 순차 게이트가 `slice_ambiguity`로 오분류되어 Gemini로 넘어오는 것을 막기 위해 가장 먼저 처리해야 합니다.
    2. **C**: G4 e2e의 기술적 마무리를 위해 `events.jsonl` 집계 로직을 추가합니다. 이는 dirty worktree 상태에서 feature를 완결 짓는 단계입니다.
    3. **B**: 모든 검증이 완료되고 기술적 결손이 해소된 시점에 Milestone 5 진입을 위한 전체 커밋 및 PR을 수행합니다.

## 추천 (RECOMMENDATION)
1. **IMPLEMENT**: `pipeline_runtime/operator_autonomy.py`의 `_MENU_CHOICE_BLOCKER_MARKERS`에 `"통과 후"`, `"완료 후"`, `"커밋"`, `"milestone"`, `"마일스톤"` 추가 및 회귀 테스트.
2. **IMPLEMENT**: `pipeline_runtime/supervisor.py`의 `_record_status_events`에서 `wrapper_models`의 `seen_task`/`accepted_task` 변화를 감지하여 `events.jsonl`에 re-emit하는 aggregation 로직 추가.
3. **NEEDS_OPERATOR**: 위 두 작업 완료 후, 전체 dirty worktree(seq 527~)에 대한 branch commit 및 push 승인 (결정 C).

---
**SOURCE**: .pipeline/gemini_request.md (seq 629)
**CONTROL_SEQ**: 630
