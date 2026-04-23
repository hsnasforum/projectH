# Advisory Log: M19 Axis 3 - Post-Learning Refinement (Durable Preference Editing)

## 개요
- **일시**: 2026-04-23
- **요청**: M19 Axis 3 (Post-Learning Refinement)의 정확한 범위 및 구현 전략 정의
- **상태**: Milestone 19의 Axis 1(증거 보존)과 Axis 2(중복 방지)가 완료됨. 이제 학습된 선호(Preference)의 내용을 사용자가 사후에도 수정할 수 있는 기능을 추가하여 개인화 루프의 "최종 제어권"을 완성할 단계임.

## 분석 및 판단
1.  **필요성**: 시스템이 자동으로 생성하거나 사용자가 리뷰 단계에서 승인한 선호 문구(`description`)가 시간이 지남에 따라 부적절해지거나 더 정밀한 표현이 필요할 수 있음. 현재는 삭제(Reject) 후 다시 학습하기를 기다려야 하는 불편함이 있음.
2.  **기능 확장**: M17에서 리뷰 단계(`ReviewQueuePanel`)에 도입했던 인라인 편집 UI를 선호 관리 단계(`PreferencePanel`)로 확장함.
3.  **데이터 일관성**: 문구가 수정되더라도 해당 선호의 고유 식별자(`fingerprint`)와 연결된 증거(Snippets)는 유지되어야 하며, `updated_at` 타임스탬프를 통해 변경 이력을 추적함.
4.  **API 설계**: 기존 상태 변경 API(`activate`, `pause` 등)와 일관성을 유지하기 위해 `POST /api/preferences/update-description` 엔드포인트를 신설함.

## 권고 사항 (RECOMMEND)
**RECOMMEND: implement M19 Axis 3 (Durable Preference Editing)**

1.  **Storage Layer (JSON/SQLite)**:
    - `PreferenceStore` 및 `SQLitePreferenceStore`에 `update_description(preference_id, description)` 메서드 추가.
    - `description`과 `updated_at` 필드를 갱신하도록 구현.
2.  **API / Handler**:
    - `app/handlers/preferences.py`에 `update_description` 핸들러 추가.
    - `app/web.py`에 `POST /api/preferences/update-description` 라우팅 추가.
3.  **Frontend (UI)**:
    - `PreferencePanel.tsx`의 각 선호 카드에 `편집` 버튼 추가.
    - 클릭 시 인라인 `textarea`를 통해 문구 수정 기능 제공.
    - `저장` 시 API를 호출하고 목록을 갱신함.
4.  **Validation**:
    - Playwright 시나리오: 활성 선호의 `편집` 클릭 -> 내용 수정 후 `저장` -> 새로고침 후에도 수정된 문구가 유지되는지 확인.

## 기대 효과
- 사용자가 자신의 개인화 프로필을 능동적으로 관리하고 정제할 수 있는 환경 제공.
- 잘못 학습된 규칙을 삭제하지 않고도 즉시 교정할 수 있어 학습 데이터 보존성 향상.
- Milestone 19의 "Durable Preference Depth and Interaction Integrity" 목표 완결.
