# 2026-04-22 milestone6-axis1-done-next-scope

## 개요
CONTROL_SEQ 785(Corrected-save bridge UI)를 통해 Milestone 6 Axis 1과 로직 하드닝(Logic Hardening) 부채가 모두 해결되었습니다. 이에 따라 (1) Axis 1의 공식 종료 및 커밋 번들 확정, (2) 다음 Milestone 6 구현 슬라이스(Axis 2)를 결정합니다.

## 중재 결과

### Q1 — Milestone 6 Axis 1 closure and commit/push bundle
**RECOMMEND: commit_push_now_bundle**
Seqs 779(Enums), 782(Artifact Linkage), 785(UI Port & Enum usage)를 통해 Milestone 6의 기초 계약(Foundation Contract)과 React UI 이식이 완료되었습니다. 특히 785 슬라이스에서 `core/agent_loop.py` 내의 잔여 리터럴 부채가 모두 청산되었음이 확인되었습니다. 이 번들은 백엔드 계약 상수의 도입부터 프론트엔드 실기능 구현까지를 관통하는 자기 완결적 단위이므로, 지금 커밋 및 푸시하여 브랜치를 안정화하는 것을 권고합니다.

### Q2 — Next concrete Milestone 6 sub-item
**NEXT SLICE: Axis 2: Truthful Content Surface - Stale Clear & Persistent Note UX**
다음 단계는 내용 거절(Content Reject) 상태의 정합성과 사용자 경험을 완성하는 것입니다.

- **Exact Sub-bullet:** `docs/MILESTONES.md` Milestone 6 "keep the shipped optional reject-note UX... appears only while the latest outcome remains `rejected`" 및 "clear it again when a later correction or explicit save supersedes `rejected`".
- **Owning Modules:**
    - `storage/session_store.py` (1050/1110행 부근): `record_correction_for_message` 및 `record_corrected_outcome_for_artifact` 메서드에서 새로운 교정이나 저장이 발생할 때 기존의 `content_reason_record`를 `pop`하여 제거(Stale Clear)하는 로직을 추가합니다.
    - `app/frontend/src/components/MessageBubble.tsx` (260행 부근): 현재 판정이 내려지면 사라지는 "내용 거절" UI를, `outcome === "rejected"`인 동안에는 메모를 수정할 수 있는 "Persistent Note Surface" 형태로 유지하도록 수정합니다.
- **Reason:** 이 작업은 Milestone 6의 핵심 목표인 "진실된 콘텐츠 인터페이스(Truthful content-surface)"를 달성하기 위한 마지막 로직 정합성 단계입니다.

## 권고 요약
1. Seqs 779+782+785 작업을 하나의 "Milestone 6 Axis 1" 번들로 커밋 및 푸시합니다.
2. 다음 슬라이스로 백엔드의 "Reject Note Stale-Clear" 로직과 프론트엔드의 "Persistent Reject Note UX"를 구현합니다.
3. 이를 통해 내용 거절 사유가 교정에 의해 상쇄되는 데이터 흐름을 완성합니다.
