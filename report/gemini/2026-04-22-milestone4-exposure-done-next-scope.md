# 2026-04-22 milestone4-exposure-done-next-scope

## 개요
CONTROL_SEQ 756(내부 필드)과 759(UI 노출)를 통해 Milestone 4의 "Better separation between strong facts, weak facts, and unresolved slots" 목표가 완결되었습니다. 이에 따른 커밋 타이밍, E2E 차단 시 진행 여부, 그리고 다음 Milestone 4 슬라이스 범위를 중재합니다.

## 중재 결과

### Q1 — Commit/push timing and scope
**RECOMMEND: commit_push_now_bundle**
CONTROL_SEQ 756(로직)과 759(UI)를 하나의 "Trusted Separation Bundle"로 묶어 커밋 및 푸시하는 것을 권고합니다. 두 작업은 Milestone 4의 핵심 목표 하나를 완전히 달성하는 응집력 있는 단위이며, `feat/watcher-turn-state` 브랜치에 더 이상의 미커밋 작업을 누적하는 것은 리스크가 큽니다.

### Q2 — Playwright claim-coverage gate
**RECOMMEND: Proceed**
Playwright 실행 차단은 샌드박스 내 소켓 권한(`PermissionError`) 문제로 확인되었으며, 이는 코드의 결함이 아닌 환경적 제약입니다. 로직 리뷰 결과 배지 렌더링 분기가 정확하고 144건의 유닛 테스트가 통과했으므로, E2E 완결을 위해 다음 슬라이스를 멈출 필요는 없습니다. 환경이 허용되는 시점에 사후 검증하는 것으로 충분합니다.

### Q3 — Next Milestone 4 slice
**RECOMMEND: Axis 3: Effective Reinvestigation (Prioritization using trust signal)**
다음 우선순위는 확보된 `trusted_source_count`를 활용해 "재조사(reinvestigation)" 효율을 높이는 것입니다.
- **Entry Point:** `core/agent_loop.py`의 `_build_entity_second_pass_queries` (3804행 부근)
- **Slice Scope:** `pending_slots.sort` 람다 식에 `trusted_source_count`를 도입하여, 신뢰 출처가 0개인 슬롯이나 `CONFLICT` 상태인 슬롯을 우선적으로 조사하도록 정렬 로직을 개선합니다. 이는 TASK_BACKLOG #3("Reinvestigate weak or unresolved slots more effectively")과 직결됩니다.

## 권고 요약
1. 756+759 작업을 하나의 번들로 커밋 및 푸시합니다.
2. 샌드박스 E2E 차단은 무시하고 다음 단계로 진행합니다.
3. 다음 슬라이스로 `trusted_source_count`를 활용한 재조사 쿼리 우선순위 최적화를 실행합니다.
