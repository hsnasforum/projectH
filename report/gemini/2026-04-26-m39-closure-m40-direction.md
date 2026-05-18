# 2026-04-26 M39 closure and M40 direction — Doc-Sync & Auditability

## 상황 개요
- **Milestone 39 (Review Context & Reasoning) 완료**: Axis 1(`context_turns`)과 Axis 2(`evidence_summary`)를 통해 리뷰 큐(Review Queue) 후보의 질적 맥락과 양적 근거를 성공적으로 보강했습니다.
- **문서 동기화 지연**: 현재 `docs/MILESTONES.md`는 Milestone 37 종결 및 Milestone 38 진행 중인 상태로 남아 있어, 실제 구현 완료된 Milestone 38/39의 상태를 반영하는 "Truth-Sync"가 필요합니다.
- **차기 방향**: 리뷰 품질 개선이 일단락되었으므로, 시스템의 학습 및 운영 투명성을 높이기 위한 **Milestone 40: Review Auditability**로 진입합니다.

## 판단 근거
1. **Truth-Sync 우선**: 인프라(M38)와 기능(M39) 라운드가 연속되면서 마일스톤 문서가 실제 코드 상태보다 뒤처져 있습니다. M40이라는 새로운 단계로 넘어가기 전 베이스라인을 정리해야 합니다.
2. **운영 투명성**: M39에서 '무엇'과 '맥락'을 보강했다면, M40에서는 '어디서(어떤 세션에서)'와 '왜(운영자의 의사결정 사유)'를 다룹니다. 이는 다수의 선호가 쌓일 때 운영 가독성을 유지하는 데 필수적입니다.
3. **리스크 관리**: 샌드박스 환경의 E2E 소켓 제약이 지속되고 있으므로, 브라우저 로직에 크게 의존하는 대규모 UI 개편보다는 데이터 모델링 및 직렬화 중심의 M40 초기 작업을 병행하는 것이 효율적입니다.

## 권고 사항 (RECOMMENDATION)
- **결정**: Milestone 39 Axis 3를 통해 문서 정합성을 맞추고 Milestone 40을 예고합니다.
- **RECOMMEND: implement Milestone 39 Axis 3: Doc-Sync Closure — M38/M39 Status Update**
    - `docs/MILESTONES.md`: Milestone 38 및 Milestone 39를 'Completed'로 이동하고 상세 내역을 갱신합니다.
    - `docs/TASK_BACKLOG.md`: 구현 완료된 항목들을 'Implemented' 섹션으로 이동합니다.
- **차기 단계 (M40)**: **Milestone 40: Review Auditability — Source Association & Decision Rationale**
    - Axis 1: 후보(Candidate)와 원본 세션 간의 딥링크(Session ID/Name) 노출.
    - Axis 2: 리뷰 승인/거절 시 운영자 사유(Rationale) 캡처 및 저장.

### 예상 결과
- 프로젝트 문서와 실제 구현 상태가 일치되어 개발/운영 흐름의 명확성 확보.
- Milestone 40을 통해 학습된 지식(Preference)의 출처와 판단 근거를 추적할 수 있는 인프라 마련.
