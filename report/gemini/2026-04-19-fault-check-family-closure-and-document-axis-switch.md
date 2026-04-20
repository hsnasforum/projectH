# 2026-04-19 fault-check family closure and document axis switch

## arbitration 결과 요약
- `fault-check` (internal operator tooling) 패밀리의 `session_recovery` consumer-contract drift가 이번 verify를 통해 docs/tests/code 전 영역에서 truthfully하게 동기화되었습니다.
- 남은 `live fault-check proof` 강화는 실제 런타임 증거를 좁히는 의미가 있으나, 해당 도구가 현재 release gate 바깥에 있다는 점과 `MILESTONES.md` 상의 "Next Phase" (structured correction memory) 진입 필요성을 고려할 때, 이 패밀리에서의 추가 micro-slice는 기회비용이 큽니다.
- 따라서 `fault-check` 패밀리를 여기서 닫고, 메인 제품 축(document-first axis)으로 돌아가 교정 메모리의 기반이 되는 `session_local_memory_signal` projection을 시작할 것을 권고합니다.

## 판단 근거
- **Truthful Closure**: `fault-check`의 `session_recovery` 데이터 구조와 gate 동작, 그리고 이를 설명하는 문서와 테스트가 모두 일치하는 상태에 도달했습니다.
- **Priority Alignment**: `GEMINI.md`의 `same-family current-risk reduction`이 Priority 1이나, `operator tooling remains outside the current release gate`라는 제약 조건 하에서 이 패밀리의 잔여 리스크(live tmux evidence)는 메인 제품의 `new quality axis` (Priority 3) 진입보다 프로젝트 전체 리스크 감소에 기여하는 바가 낮습니다.
- **Next Phase Step**: `TASK_BACKLOG.md`의 "Next To Add" 중 `session_local_memory_signal`은 기존 grounded-brief와 approval/save trace를 연결하는 읽기 전용 레이어로, 위험도가 낮으면서도 후속 `durable preference memory` 구현의 필수 관문입니다.

## 권고 slice
- `RECOMMEND: close fault-check family and switch axis to document-first memory signals`
- **SLICE**: `implement read-only session_local_memory_signal projections for grounded-brief traces`
- **SCOPE**:
  - `session_local_memory_signal` 데이터 구조 정의 (grounded-brief anchor + approval/save outcome 연결)
  - 기존 세션 trace로부터 해당 신호를 추출하는 읽기 전용 projection logic 구현
  - 세션 serialization 및 JSON payload에 해당 신호 노출
- **VERIFICATION**:
  - 기존 grounded-brief trace를 포함한 mock session을 통한 projection 정확도 unit test
  - JSON schema 회귀 테스트 (기존 contract 파괴 여부 확인)
