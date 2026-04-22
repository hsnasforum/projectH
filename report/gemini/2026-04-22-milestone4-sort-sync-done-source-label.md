# 2026-04-22 milestone4-sort-sync-done-source-label

## 개요
CONTROL_SEQ 768(AgentLoop 정렬 로직 동기화)이 완료됨에 따라, (1) Milestone 4의 잔여 작업 확인, (2) 현재까지의 작업 번들 커밋 여부, (3) 차기 단계(Milestone 5) 진입 시점을 결정합니다.

## 중재 결과

### Q1 — Milestone 4 completion status after seq 768
**Milestone 4는 95% 완료되었으며, "source role labeling" UI 구현만 남았습니다.**
- **의미:** `core/agent_loop.py`는 이미 `source_role`(예: "공식 기반") 데이터를 API로 내려주고 있습니다. 하지만 `MessageBubble.tsx`는 현재 슬롯 이름과 상태 기호(`✓`, `?`, `-`)만 보여줄 뿐, 해당 정보가 어떤 성격의 출처에서 왔는지(Role)는 숨겨져 있습니다.
- **Next Slice:** **Source Role UI Labeling**
    - **Entry Point:** `app/frontend/src/components/MessageBubble.tsx` (315행 부근)
    - **Scope:** 클레임 커버리지 배지에 마우스를 올렸을 때(tooltip)나 배지 텍스트 옆에 `item.source_role`을 표시하여 정보의 출처 신뢰도를 사용자에게 가시화합니다.

### Q2 — Commit/push now
**RECOMMEND: commit_push_now_bundle**
이미 완료된 Seqs 756, 759, 762, 765, 768은 "엔티티 카드 조사 품질 및 논리 정합성"을 완성하는 견고한 논리 번들입니다. 브랜치 안정성을 위해 이 시점에서 한 번 커밋 및 푸시를 수행하여 "Logic Hardening" 단계를 닫고, 이후 순수 UI 개선 슬라이스로 넘어가는 것이 바람직합니다.

### Q3 — If Milestone 4 "source role labeling" is the last remaining item
**네, 해당 UI 슬라이스가 Milestone 4의 마지막 항목입니다.**
`docs/MILESTONES.md`의 Milestone 4 항목 중 "source role labeling"을 제외한 모든 항목(shaping, coverage, reinvestigation, weighting, separation)이 논리와 데이터 수준에서 완료되었습니다. UI 표시까지 완료되면 Milestone 4가 최종 클로징되며, 이후 **Milestone 5: Grounded Brief Contract**로의 전환이 가능해집니다.

## 권고 요약
1. 현재까지의 756~768 작업을 하나의 번들로 커밋 및 푸시합니다.
2. 다음 슬라이스로 `MessageBubble.tsx`에서 `source_role`을 UI에 노출하는 작업을 진행합니다.
3. UI 노출 작업 완료 후 Milestone 4를 종료하고 Milestone 5로 이행합니다.
