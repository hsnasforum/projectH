# Advisory Log: M18 Definition - Cross-Session Signal Infrastructure

## 개요
- **일시**: 2026-04-23
- **요청**: M17 종료 이후 M18 범위 정의 및 차기 슬라이스 추천
- **상태**: Milestone 17(Personalization Refinement)이 27개의 커밋과 함께 성공적으로 병합(PR #31) 및 종료됨. 다음 단계는 "Next Implementation Priorities"에 따라 세션 경계를 넘어서는 신호 발견(Cross-Session Signal Discovery)으로 진입함.

## 분석 및 판단
1.  **기술적 제약**: 현재 `CorrectionStore`는 8,000개 이상의 JSON 파일로 구성되어 있음. 세션 간 반복되는 교정 패턴을 실시간으로 검색하거나 집계하기에는 성능상 한계가 명확함.
2.  **전제 조건 (Pre-requisite)**: 효율적인 교차 세션 분석을 위해서는 `CorrectionStore`의 SQLite 이관이 필수적임. 현재 `Session`, `Artifact`, `Preference` 등은 이미 SQLite seam이 있으나 `Correction`만 JSON-only 상태임.
3.  **M18 방향성**: "Cross-Session Signal Infrastructure"
    - 개별 세션에 갇혀 있는 교정 데이터를 통합 저장소로 모으고, 이를 바탕으로 세션 간 반복되는 패턴을 "발견"하는 기초 체력을 확보함.
4.  **M18 슬라이스 구성**:
    - **Axis 1 (Integrity)**: SQLite Correction Store Parity. (교정 저장소의 SQLite 지원 및 성능 최적화)
    - **Axis 2 (Discovery)**: Cross-session Recurrence Indexing. (SQL을 이용한 세션 간 지문 집계 로직)
    - **Axis 3 (Surface)**: Global Candidate Review Interface. (여러 세션에 걸친 후보를 리뷰 큐에 노출)

## 권고 사항 (RECOMMEND)
**RECOMMEND: implement M18 Axis 1 (SQLite Correction Store Parity)**

1.  **Storage Layer**:
    - `storage/sqlite_store.py`에 `SQLiteCorrectionStore` 클래스 추가.
    - 기존 `CorrectionStore` (JSON) 인터페이스와 100% 호환되는 CRUD 메서드 구현.
    - `find_by_fingerprint` 및 `find_by_artifact`를 SQL 쿼리로 전환하여 성능 향상.
2.  **Migration**:
    - `storage/migrate.py`에 corrections 테이블 이관 로직 추가.
3.  **Validation**:
    - JSON vs SQLite 백엔드 간의 데이터 정합성 단위 테스트.
    - 8,000+ 레코드 기준의 조회 성능 벤치마크 (기존 JSON 방식 대비 개선 확인).

## 기대 효과
- 수만 개의 교정 데이터도 지연 없이 집계 가능한 성능 확보.
- Milestone 18의 핵심인 "세션 간 패턴 발견"을 위한 데이터 기반 마련.
- 저장소 레이어의 완벽한 SQLite 통합으로 향후 JSON 백엔드 제거의 기틀 마련.
