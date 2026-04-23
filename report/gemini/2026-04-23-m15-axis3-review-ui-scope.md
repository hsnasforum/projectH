# Advisory Log: M15 Axis 3 - Review Queue List/Detail UI Scope

## 개요
- **일시**: 2026-04-23
- **요청**: M15 Axis 3 (Review Queue List/Detail UI)의 정확한 범위 및 구현 전략 정의
- **상태**: 현재 `ChatArea` 헤더에 "리뷰 N건" 숫자 배지만 존재하며 개별 항목을 조회하거나 처리할 UI가 없음. M14/M15 Axis 1을 통해 백엔드 데이터와 API는 준비된 상태임.

## 분석 및 판단
1.  **UX 방향**: 숫자 배지는 단순 알림을 넘어, 클릭 시 상세 목록으로 진입하는 트리거 역할을 수행해야 함. 
2.  **구조적 배치**: `PreferencePanel`과 유사하게 `Sidebar` 내에 상주하는 `ReviewQueuePanel` 섹션을 추가하는 것이 관리 효율적임. 선호 기억(Preference)과 검토 후보(Candidate)는 "Personalization Memory"라는 하나의 논리적 그룹으로 묶일 수 있음.
3.  **컴포넌트 분리**: `ReviewQueuePanel.tsx`를 신규 생성하여 독립성을 유지하고, `Sidebar.tsx`에서 이를 호출함.
4.  **인터랙션**:
    - `ChatArea.tsx`의 리뷰 배지를 `button`으로 변경.
    - 클릭 시 사이드바가 닫혀있으면 열고, `ReviewQueuePanel` 섹션을 확장(Expand)함.
5.  **기능 상세**:
    - 각 후보 카드: `statement` (제안된 선호 문구) 표시.
    - 품질 정보: `is_high_quality`인 경우 `고품질` 배지 노출.
    - 액션 버튼: `수락`, `보류`, `거절` (기존 `/api/candidate-review` 호출).
    - 수락 시: 해당 항목은 목록에서 사라지고 `PreferencePanel` 목록에 나타남 (새 세션 로드 필요).

## 권고 사항 (RECOMMEND)
**RECOMMEND: implement M15 Axis 3 (Review Queue List UI)**

1.  **New Component**: `app/frontend/src/components/ReviewQueuePanel.tsx` 생성.
    - `review_queue_items`를 프롭으로 받아 렌더링.
    - `onReviewAction` 콜백을 통해 `postCandidateReview` 실행 및 세션 갱신.
2.  **Sidebar Integration**:
    - `Sidebar.tsx`에 `ReviewQueuePanel` 장착 (위치는 `PreferencePanel` 바로 위).
    - `expanded` 상태 관리를 통해 사용자 선택 시에만 노출.
3.  **ChatArea Badge Expansion**:
    - 헤더 배지를 버튼으로 래핑.
    - `onOpenReviewQueue` 프롭 추가 (App.tsx에서 사이드바 열기 및 섹션 확장 제어).
4.  **Validation**:
    - Playwright 시나리오: 헤더 배지 클릭 -> 목록 노출 확인 -> 수락 버튼 클릭 -> 배지 카운트 감소 및 목록에서 제거 확인.

## 기대 효과
- 사용자가 시스템이 제안한 교정 패턴을 명시적으로 검토하고 수락할 수 있는 완전한 피드백 루프 완성.
- Milestone 15의 "Review Surface Expansion" 목표 달성.
