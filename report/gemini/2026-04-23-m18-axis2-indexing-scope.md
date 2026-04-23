# Advisory Log: M18 Axis 2 - SQL-based Cross-Session Recurrence Indexing Scope

## 개요
- **일시**: 2026-04-23
- **요청**: M18 Axis 2 (SQL-based Cross-Session Recurrence Indexing)의 정확한 범위 및 구현 전략 정의
- **상태**: M18 Axis 1에서 `SQLiteCorrectionStore` 기본 인터페이스와 데이터 이관 로직이 성공적으로 배포됨. 현재 8,029개의 교정 레코드가 JSON 파일로 존재하며, 이를 검색하고 집계하는 로직의 성능 최적화가 다음 과제임.

## 분석 및 판단
1.  **성능 병목 해소**: 기존 JSON 기반 `find_recurring_patterns`는 모든 파일을 읽어 메모리에서 집계하므로 데이터 증가에 따라 선형적으로 느려짐(O(n)). SQLite의 인덱싱된 `delta_fingerprint` 컬럼을 활용하면 이를 데이터베이스 레벨에서 효율적으로 처리할 수 있음.
2.  **서버 활성화 (Server Wiring)**: 준비된 `SQLiteCorrectionStore`를 실제 런타임 서버(`app/web.py`)에 연결하여, SQLite 백엔드 사용자가 즉각적인 성능 향상을 체감할 수 있도록 함.
3.  **교차 세션 분석 기반**: `GROUP BY delta_fingerprint` 쿼리를 통해 여러 세션에 걸쳐 나타나는 동일 패턴을 발견하는 "글로벌 후보 발견"의 기술적 토대를 완성함.

## 권고 사항 (RECOMMEND)
**RECOMMEND: implement M18 Axis 2 (SQL-based Recurrence Indexing & Server Wiring)**

1.  **Storage Layer (SQL Efficiency)**:
    - `storage/sqlite_store.py`의 `SQLiteCorrectionStore`에 `find_recurring_patterns(session_id=None)` 구현.
    - SQL `GROUP BY` 및 `HAVING COUNT(*) >= 2` 절을 사용하여 반복 패턴을 식별.
    - 결과 데이터는 기존 `CorrectionStore` (JSON)와 호환되는 `list[dict]` 형태를 유지 (상세 레코드 목록 포함).
2.  **Server Integration (Wiring)**:
    - `app/web.py`에서 `storage_backend == "sqlite"`인 경우 `SQLiteCorrectionStore`를 인스턴스화하여 `self.correction_store`에 할당.
    - 이로 인해 `find_by_artifact` (Review Queue), `find_by_fingerprint` (Preference promotion) 등 모든 조회 경로가 SQL을 사용하게 됨.
3.  **Validation**:
    - JSON vs SQLite 저장소 간의 `find_recurring_patterns` 결과 정합성 테스트.
    - 여러 세션에 걸친 동일 패턴이 SQL 쿼리에 의해 정확히 집계되는지 확인하는 단위 테스트 추가.

## 기대 효과
- 8,000개 이상의 교정 데이터 집계 속도가 초 단위에서 밀리초 단위로 개선.
- 세션 로드 및 리뷰 큐 렌더링 시의 I/O 부하 대폭 감소.
- Milestone 18 Axis 3 (글로벌 후보 UI) 구현을 위한 신뢰할 수 있는 데이터 인터페이스 확보.
