# Advisory Log: M21 Definition - Personalization Maturity and Release Bundle

## 개요
- **일시**: 2026-04-23
- **요청**: M20 종료 이후 M21 범위 정의 (m20_closed_m21_scope_needed)
- **상태**: Milestone 20(Personalization Scaling)이 성공적으로 종료됨. 현재 `origin/main` 대비 40개 이상의 커밋(Milestones 18~20)이 누적되었으며, 아키텍처는 SQLite 기반으로 완전히 성숙함. 이제 기능적 공백을 메우고 대규모 변경 사항을 통합할 단계임.

## 분석 및 판단
1.  **기술적 완결성 (Storage Parity)**: M18 Axis 1에서 구축한 `SQLiteCorrectionStore`에 아직 `confirm`, `promote`, `activate` 등 상태 전이(Lifecycle transition) 메서드들이 누락되어 있음. 이는 JSON 저장소와의 완전한 교체(Drop-in replacement)를 가로막는 마지막 공백임.
2.  **운영 무결성 (Negative Signal Audit)**: 현재 "글로벌 후보(Global Candidate)"에 대한 거절(Reject)이나 보류(Defer) 액션은 `task_logger`에만 기록될 뿐, 영구적으로 저장되지 않음. 이로 인해 사용자가 거절한 후보가 다음 세션에서 다시 나타나는 노이즈(Noise) 리스크가 있음. 거절된 후보를 `PreferenceStore`에 `REJECTED` 상태로 기록하여 재발을 방지해야 함.
3.  **병합 및 릴리스 (Release Bundle)**: M18부터 M20까지 누적된 40+ 커밋은 시스템의 핵심 아키텍처(SQLite 전환)와 사용자 경험(글로벌 리뷰, 인라인 편집)을 대폭 변경함. PR #31(M13-17) 이후의 이 거대한 변경 묶음을 하나의 "Personalization Release Bundle"로 정의하고, 최종 검증 후 메인 브랜치 병합을 추진해야 함.

## 권고 사항 (RECOMMEND)
**RECOMMEND: implement M21 Axis 1 (SQLite Correction Lifecycle Maturity)**

1.  **Storage Layer**:
    - `storage/sqlite_store.py:SQLiteCorrectionStore`에 `confirm_correction`, `promote_correction`, `activate_correction`, `stop_correction` 메서드 추가.
    - JSON 저장소의 `_transition` 로직을 SQL `UPDATE` 문으로 구현하여 상태 및 타임스탬프 갱신.
2.  **Validation**:
    - SQLite 환경에서 교정 레코드의 수명 주기 전이가 정확히 수행되는지 단위 테스트 검증.
    - 기존 8,000+ 이관 데이터와의 호환성 확인.

**M21 전체 로드맵 계획**:
- **Axis 2 (Control)**: 글로벌 후보 거절 시 `PreferenceStore`에 `REJECTED` 상태로 영구 기록하여 리뷰 큐 노이즈 차단.
- **Axis 3 (Consolidation)**: M18~M21 통합 묶음에 대해 142개 이상의 Smoke Test 전수 재검증 및 PR #32 병합 권고.

## 기대 효과
- 저장소 레이어의 완벽한 SQLite 전환 완료 및 기술적 부채 청산.
- 사용자 피드백(거절)의 영구 반영을 통해 개인화 시스템의 정직성과 효율성 증대.
- 대규모 아키텍처 변경을 안전하게 제품에 반영하기 위한 검증된 릴리스 기반 마련.
