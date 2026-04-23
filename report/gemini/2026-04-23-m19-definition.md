# Advisory Log: M19 Definition - Durable Preference Depth and Interaction Integrity

## 개요
- **일시**: 2026-04-23
- **요청**: M18 종료 이후 M19 범위 정의 (m18_closed_m19_scope_needed)
- **상태**: Milestone 18(Cross-Session Signal Infrastructure)을 통해 세션 경계를 넘는 교정 패턴 발견 및 글로벌 후보 리뷰 체계가 구축됨. 이제 학습된 "선호(Preference)"의 사후 관리와 무결성(Integrity)을 강화할 단계임.

## 분석 및 판단
1.  **증거 손실 (Evidence Loss)**: 현재 `ReviewQueuePanel`에서는 교정 전후 스니펫을 상세히 보여주지만, 수락되어 `Preference`로 승격되는 순간 이 상세 증거가 소실됨. `PreferencePanel`에서도 "왜 이 규칙이 생겼는지"를 영구적으로 확인할 수 있어야 함 (정직성 원칙).
2.  **중복 및 충돌 리스크**: 글로벌 후보 발견이 활성화되면서, 이미 존재하는 선호와 유사하거나 중복되는 후보가 리뷰 큐에 다시 나타날 가능성이 높아짐. 후보 기록 시 기존 선호와의 중복 여부를 엄격히 체크해야 함.
3.  **사용자 제어권 확장**: 사용자가 한 번 수락한 선호 문구(`description`)를 나중에라도 미세 조정(Editing)할 수 있는 기능이 필요함. 이는 M17에서 리뷰 단계에 도입된 편집 기능을 선호 관리 단계로 확장하는 것임.
4.  **M19 방향성**: "Durable Preference Depth and Interaction Integrity"
    - 선호의 근거를 보존하고(Depth), 중복을 방지하며(Integrity), 사후 편집 권한을 부여함(Control).

## 권고 사항 (RECOMMEND)
**RECOMMEND: implement M19 Axis 1 (Preference Evidence Persistence)**

1.  **Storage Layer (JSON/SQLite)**:
    - `PreferenceStore` 및 `SQLitePreferenceStore`의 promotion 로직(`promote_from_corrections`, `record_reviewed_candidate_preference`) 수정.
    - 소스 교정본에서 `original_snippet`과 `corrected_snippet`을 추출하여 선호 레코드에 함께 저장하도록 보강.
2.  **UI (PreferencePanel)**:
    - `PreferencePanel.tsx`에 `ReviewQueuePanel`과 동일한 `상세 보기` / `접기` 토글 추가.
    - 저장된 스니펫이 있을 경우 원문과 교정본 대조 뷰 렌더링.
3.  **Validation**:
    - Playwright 시나리오: 글로벌 후보 수락 -> 설정창(사이드바) 이동 -> 해당 선호의 '상세 보기' 클릭 -> 교정 전후 스니펫이 정상 노출되는지 확인.

**M19 전체 로드맵 계획**:
- **Axis 2 (Integrity)**: 신규 후보 기록 시 기존 Fingerprint/Statement 중복 검사 강화.
- **Axis 3 (Control)**: `PreferencePanel` 내 선호 문구 인라인 편집 기능.

## 기대 효과
- 학습된 모든 개인화 규칙에 대해 영구적이고 구체적인 판단 근거 제공.
- 시스템이 내린 결정을 사용자가 언제든 검증하고 수정할 수 있는 신뢰 환경 구축.
- Milestone 19의 "Depth and Integrity" 목표 달성.
