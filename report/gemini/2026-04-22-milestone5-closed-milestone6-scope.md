# 2026-04-22 milestone5-closed-milestone6-scope

## 개요
CONTROL_SEQ 775(Content Reject Parent Wire-up)를 통해 Milestone 5 "Grounded Brief Contract"가 최종 완료되었습니다. 이에 따라 (1) Milestone 5 종료 선언, (2) Seqs 756~775 통합 커밋 범위 확인, (3) 차기 단계인 Milestone 6 "Minimum Correction / Approval / Preference Memory Contract"의 첫 구현 슬라이스를 중재합니다.

## 중재 결과

### Q1 — Milestone 5 closure
**RECOMMEND: milestone5_closed**
Seqs 774~775를 통해 React 프론트엔드에 "내용 거절(Content Verdict)" 및 "거절 메모(Reject Note)" 인터페이스가 구현되어, Milestone 5의 마지막 "still later" 항목인 "keep the first optional reject-note surface narrow"가 충족되었습니다. 또 다른 항목인 "keep corrected-save bridge expansion narrow"는 구현 대상이 아닌 설계 제약(constraint directive)이므로, Milestone 5는 이 시점에서 공식적으로 종료됩니다.

### Q2 — Commit/push bundle scope
**RECOMMEND: commit_push_now_bundle**
Seqs 756~775 전체를 하나의 번들로 커밋 및 푸시하는 것을 권고합니다. Seqs 756~771(Milestone 4: 조사 품질 강화)과 Seqs 774~775(Milestone 5: 내용 거절 UI React 이식)는 모두 응집력 있는 기능 단위이며, 백엔드 로직과 프론트엔드 UI가 상호 검증되었습니다. Milestone 6의 새로운 로직 변경을 시작하기 전에 `feat/watcher-turn-state` 브랜치를 깨끗하게 안정화하는 것이 위험 관리 차원에서 바람직합니다.

### Q3 — First Milestone 6 entry slice
**NEXT SLICE: Axis 1: Richer Scoped Reason Records (Contract & Backend)**
Seqs 774~775로 "진실된 사용자 입력 인터페이스(truthful user-input surface)"가 React 앱에 확보됨에 따라, `TASK_BACKLOG.md` #35행의 제약이 해소되었습니다. 다음 우선순위는 하드코딩된 최소 라벨을 고도화된 계약(contract) 기반 라벨 시스템으로 확장하는 것입니다.

- **Exact Sub-bullet:** `docs/MILESTONES.md` Milestone 6 "define shared reason fields with distinct correction / reject / reissue label sets" 및 `docs/TASK_BACKLOG.md` Next To Add #4 ("Richer scoped reason records...").
- **Owning Modules:**
    - `core/contracts.py` (line 125 부근): `ContentReasonLabel`, `ApprovalReasonLabel` 클래스 정의 및 허용 라벨 세트(Set) 확장.
    - `storage/session_store.py` (line 1175 부근): `record_rejected_content_verdict_for_message` 등에서 `"explicit_content_rejection"`과 같은 하드코딩된 문자열을 계약 기반 상수로 교체.
- **Reason:** 풍부한 사유 기록은 차후 "Durable Preference Memory"를 구축하기 위한 필수적인 데이터 자산(Asset)입니다.

## 권고 요약
1. Seqs 756~775 작업을 하나의 번들로 커밋 및 푸시하여 Milestone 5를 공식 클로징합니다.
2. 다음 슬라이스로 `core/contracts.py`와 `session_store.py`를 수정하여 내용 거절 및 수정에 대한 풍부한 사유 라벨 시스템을 구축합니다.
3. 확보된 데이터 기반을 바탕으로 향후 Milestone 6의 메모리 신호(Memory Signal) 고도화로 나아갑니다.
