# Advisory Log: M17 Definition - Personalization Refinement (Editing & Evidence Detail)

## 개요
- **일시**: 2026-04-23
- **요청**: M16 완료 이후 M17 범위 정의 (m16_closed_m17_scope_needed)
- **상태**: M16(Review Depth and Reliability)을 통해 리뷰 증거(delta_summary) 노출과 UI 회복탄력성이 확보됨. 현재 21개 커밋이 누적된 상태이며, 개인화 루프의 기본 기능은 완성되었으나 사용자의 "미세 조정" 능력이 부족함.

## 분석 및 판단
1.  **리뷰 액션 완결성**: 현재 `accept`, `reject`, `defer`는 구현되어 있으나, 시스템이 제안한 문구를 사용자가 직접 수정하는 `edit` 기능이 누락됨. 이는 `docs/MILESTONES.md`에서 "later stage"로 분류되어 있던 항목임.
2.  **증거 가시성 심화**: M16에서 `delta_summary`를 추가했으나, 실제 "어떤 문장이 어떻게 바뀌었는지"에 대한 구체적인 스니펫(Snippet) 비교는 여전히 불가능함. `ReviewQueuePanel`에서 카드를 확장하여 상세 내역을 볼 수 있는 기능이 필요함.
3.  **릴리스 전략**: 21개 커밋이 main 브랜치 대비 앞서 있으므로, M17은 기능 구현과 동시에 "Release Stabilization"을 목표로 삼아야 함. M16에서 수행한 `make e2e-test` PASS 상태를 유지하며 최종 PR 준비 단계로 진입함.
4.  **M17 방향성**: "Personalization Refinement: Editing and Evidence Detail"
    - 사용자가 개인화 규칙을 수동으로 편집(Edit)할 수 있게 하고, 더 깊은 증거(Evidence Detail)를 제공하여 학습의 정확도를 높임.

## 권고 사항 (RECOMMEND)
**RECOMMEND: implement M17 Axis 1 (Review Statement Editing)**

1.  **Frontend (UI)**:
    - `ReviewQueuePanel.tsx`에서 각 카드에 `편집` 버튼 추가.
    - 클릭 시 `statement`를 수정할 수 있는 인라인 텍스트 영역(Textarea) 노출.
2.  **API/Handler**:
    - `postCandidateReview` API가 수정된 `statement`를 전달받을 수 있도록 보강.
    - 백엔드(`app/handlers/aggregate.py`)에서 `edit` 액션 시 `durable_candidate.statement`를 갱신하도록 구현.
3.  **Validation**:
    - Playwright 시나리오: 리뷰 카드에서 `편집` 클릭 -> 문구 수정 -> `수락` -> 선호 기억 패널에 수정된 문구로 반영되는지 확인.

**M17 전체 로드맵 계획**:
- **Axis 2 (Detail View)**: 리뷰 카드 확장 시 `original` vs `corrected` 스니펫 비교 노출.
- **Axis 3 (Stability)**: 누적된 21+ 커밋에 대한 최종 릴리스 검증 및 PR 생성 권고.

## 기대 효과
- 사용자가 시스템의 제안을 수동적으로 수락하는 대신, 자신의 의도에 맞게 규칙을 정제 가능.
- 개인화 학습 데이터의 품질(Statement Accuracy) 향상.
- 대규모 변경 묶음을 안전하게 릴리스할 수 있는 토대 마련.
