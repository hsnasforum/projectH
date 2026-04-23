# Advisory Log: M15 Definition - Personalization Stability & Review Surface Expansion

## 개요
- **일시**: 2026-04-23
- **요청**: M14 완료 이후 M15 범위 정의 (m14_closed_m15_scope_needed)
- **상태**: M14(Personalization Integrity & Trace Quality Integration)가 성공적으로 종료됨. Axes 1-3을 통해 SQLite auto-activation parity, PreferencePanel 및 Review Queue count의 품질 배지 통합이 완료됨.

## 분석 및 판단
1.  **잔여 리스크 및 부채**:
    - **SQLite Quality Gap**: M14 Axis 2에서 JSON-backend에는 적용된 `avg_similarity_score`가 SQLite manual review accept 경로(`record_reviewed_candidate_preference`)에는 누락됨. 이는 데이터 일관성(Integrity) 측면에서 최우선 해결 과제임.
    - **UI 검증 부족**: M14에서 추가된 고품질 배지 UI 요소들에 대한 Playwright smoke test가 부재함.
    - **Review Queue 기능 제약**: 현재 Review Queue는 `ChatArea`의 숫자 배지로만 존재하며, 각 항목의 상세 내용을 확인하거나 개별 액션(Accept/Reject/Defer)을 수행할 전용 패널이 없음.
2.  **M15 방향성**: "Personalization Stability & Review Surface Expansion"
    - M14에서 확보한 품질 축(Quality Axis)을 기술적으로 공고히 하고(SQLite Parity & Tests), 사용자 경험을 "목록화" 단계로 확장함.
3.  **M15 슬라이스 구성**:
    - **Axis 1 (Integrity)**: SQLite PreferenceStore Quality Parity.
    - **Axis 2 (Risk Reduction)**: M14 UI 변경점(Quality Badges)에 대한 Playwright Smoke Test 보강.
    - **Axis 3 (UX Expansion)**: Review Queue 상세 목록 패널 (First Slice).

## 권고 사항 (RECOMMEND)
**RECOMMEND: implement M15 Axis 1 (SQLite Quality Parity)**

1.  **Storage Layer**:
    - `storage/sqlite_store.py`의 `SQLitePreferenceStore.record_reviewed_candidate_preference`가 `avg_similarity_score`를 저장/갱신하도록 업데이트.
    - 수동 리뷰 수락 시에도 `similarity_score`를 전달받아 평균값을 계산하거나, `artifact_id`를 통해 `CorrectionStore`에서 점수를 조회하는 로직 구현.
2.  **API/Handler**:
    - 리뷰 수락 API 호출 시 백엔드에서 해당 후보의 품질 점수를 함께 처리하도록 보강.
3.  **Validation**:
    - SQLite 환경에서의 `avg_similarity_score` 저장 및 `quality_info` 노출 여부 단위 테스트 검증.

## 기대 효과
- 모든 스토리지 백엔드(JSON/SQLite) 간의 품질 데이터 정합성 확보.
- 향후 Review Queue 확장 시 기반이 되는 데이터의 신뢰도 향상.
