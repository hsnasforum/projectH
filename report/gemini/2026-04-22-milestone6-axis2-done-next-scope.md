# 2026-04-22 milestone6-axis2-done-next-scope

## 개요
CONTROL_SEQ 789(Stale Clear & Persistent Note UX)가 완료됨에 따라, (1) Milestone 6 Axis 1-2 통합 커밋 범위, (2) 다음 Milestone 6 구현 슬라이스(Axis 3)를 결정합니다.

## 중재 결과

### Q1 — Milestone 6 Axis 2 closure and commit/push
**RECOMMEND: commit_push_now_bundle**
Seqs 779~785(기초 계약 및 UI 이식)와 789(상태 동기화 및 지속적 노트 UX)는 "진실된 콘텐츠 인터페이스(Truthful content-surface)"를 구축하는 하나의 완성된 논리적 단위입니다. 백엔드에서 사유 라벨 상수를 정립하고, 아티팩트 상태를 동기화하며, 프론트엔드에서 이를 실동작하는 UI로 구현한 이 모든 과정이 상호 검증되었습니다. 브랜치의 안정성을 확보하고 다음 단계의 "데이터 고도화"로 나아가기 위해 이 시점에서 통합 커밋 및 푸시를 수행할 것을 권고합니다.

### Q2 — Next concrete Milestone 6 sub-item
**NEXT SLICE: Axis 3: Richer Scoped Reason Records (Expansion)**
Axis 2를 통해 "진실된 사용자 입력 인터페이스"가 확보됨에 따라, 하드코딩된 최소 라벨 세트를 확장할 수 있는 환경이 마련되었습니다 (`TASK_BACKLOG.md` #35 제약 해소).

- **Exact Sub-bullet:** `docs/MILESTONES.md` Milestone 6 "define shared reason fields with distinct correction / reject / reissue label sets" 및 `docs/TASK_BACKLOG.md` Next To Add #4 ("Richer scoped reason records... beyond the current minimum labels").
- **Owning Modules:**
    - `core/contracts.py` (line 251 부근): `ContentReasonLabel`에 `FACT_ERROR`, `TONE_ERROR`, `MISSING_INFO` 등의 구체적 사유 추가.
    - `app/frontend/src/components/MessageBubble.tsx` (line 336 부근): 내용 거절 영역에 텍스트 메모 외에 위에서 정의한 구체적 사유를 선택할 수 있는 칩(Chip) 또는 드롭다운 UI 추가.
- **Reason:** 풍부한 사유 데이터는 향후 Milestone 6의 핵심 목표인 "세션 로컬 메모리 신호(Session-local memory-signal)"의 품질을 결정짓는 핵심 자산입니다.

## 권고 요약
1. Seqs 779~789 전체 작업을 "Milestone 6 Truthful Surface Bundle"로 묶어 커밋 및 푸시합니다.
2. 다음 슬라이스로 `core/contracts.py`와 `MessageBubble.tsx`를 수정하여 내용 거절 시 구체적인 사유(사실 오류, 문체 불만족 등)를 선택할 수 있는 기능을 구현합니다.
3. 이를 통해 단순 거절 기록을 넘어, 사용자의 거절 의도(Intent)를 정형화된 데이터로 포착하기 시작합니다.
