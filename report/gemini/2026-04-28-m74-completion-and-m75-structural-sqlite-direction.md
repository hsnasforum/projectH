# Advisory Log: 2026-04-28 — M74 완료 및 M75 SQLite 스토어 구조 분해(Structural Decomposition) 방향 권고

## 개요
M74 (Artifact & TaskLog Validation) 번들 구현 및 검증이 완료되었습니다. 이로써 교정(Correction), 선호도(Preference), 아티팩트(Artifact), 태스크 로그(TaskLog) 등 주요 로컬 저장소의 읽기 경로에 대한 물리 검증(Physical Validation) Axis가 성공적으로 마무리되었습니다. 본 advisory는 "v1.5 structural" 단계의 연장선상에서, 비대해진 SQLite 스토어 통합 파일을 책임별로 분리하는 M75 구조 개선 슬라이스를 권고합니다.

## 분석 및 상태 확인
- **M74 성과**: 아티팩트와 태스크 로그의 읽기 경로에 정합성 검사 가드레일을 추가하여 데이터 계층의 신뢰도를 높였습니다. (verify CONTROL_SEQ 1265)
- **구조적 부채**: `storage/sqlite_store.py`는 현재 약 1,100라인에 달하며, 세션(Session), 태스크 로그(TaskLog), 아티팩트(Artifact), 선호도(Preference), 교정(Correction) 등 5개 이상의 서로 다른 스토어 구현체가 하나의 파일에 혼재되어 있습니다.
- **패턴 일관성**: M70에서 핸들러 계층(`aggregate.py`)을 `corrections.py` 등으로 분리한 것과 동일한 논리로, 데이터 계층 역시 책임별로 모듈화하여 유지보수성을 확보해야 합니다.

## 권고 사항
`RECOMMEND: structural M75 Axis 1 — SQLite Store Structural Decomposition`

### 권고 근거
1. **내부 정리 (Internal Cleanup)**: 단일 파일에 집중된 책임을 분산시켜 코드 가독성과 유지보수성을 향상시킵니다. (Priority 4: internal cleanup / v1.5 structural 지침 준수)
2. **패턴 대칭성**: 핸들러(Handler) 계층의 분리 패턴을 스토어(Store) 계층으로 확장하여 아키텍처적 일관성을 완성합니다.
3. **위험 감소**: 향후 특정 스토어의 스키마 변경이나 기능 확장이 다른 스토어 구현체에 영향을 주지 않도록 격리(Isolation) 수준을 높입니다.

### M75 Axis 1 상세 가이드
- **작업 내용**:
  - `storage/sqlite/` 디렉토리 신규 생성.
  - `storage/sqlite_store.py`에서 각 스토어 구현체(`SQLiteSessionStore`, `SQLiteArtifactStore` 등)를 개별 파일로 추출.
  - `SQLiteDatabase` (공통 DB 연결 관리)를 `storage/sqlite/base.py`로 이동.
  - 기존 `storage/sqlite_store.py`는 역임포트(Re-export) 또는 호환성을 위한 래퍼로 남기거나, 점진적으로 참조를 업데이트.
- **범위**: Pure Refactoring (동작 변경 없음).

## 결론
데이터 계층의 물리적 검증(M72-M74)이 완료됨에 따라, 이를 담는 그릇인 코드 구조를 정리하는 M75 Axis 1 진행을 권고합니다. 이 작업은 "v1.5 structural" 단계의 마침표가 될 것이며, 이후에는 선호도 주입 신뢰도(Axis 3) 또는 대규모 기능 전환이 가능해질 것입니다.
