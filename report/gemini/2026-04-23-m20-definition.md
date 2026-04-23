# Advisory Log: M20 Definition - Personalization Scaling and Conflict Integrity

## 개요
- **일시**: 2026-04-23
- **요청**: M19 종료 이후 M20 범위 정의 (m19_closed_m20_scope_needed)
- **상태**: Milestone 19(Durable Preference Depth)가 성공적으로 종료됨. 현재 `origin/main` 대비 40개 이상의 커밋이 누적된 상태이며, 개인화 시스템의 데이터 규모(8,000+ 교정 레코드)와 복잡성이 증가함에 따라 시스템의 확장성(Scaling)과 상충(Conflict) 관리 능력을 강화할 단계임.

## 분석 및 판단
1.  **확장성 부채 (Scaling Debt)**: M18에서 `SQLiteCorrectionStore`를 구축했으나, 여전히 기존 8,029개의 JSON 교정 파일이 기본 저장소로 사용되거나 파편화되어 있음. 대규모 데이터를 처리하는 개인화 시스템으로서 SQLite 백엔드를 완전히 정착시키고 성능을 최적화해야 함.
2.  **상충 관리 (Conflict Integrity)**: 사용자가 선호 문구를 직접 편집(M19)하고 글로벌 후보를 수락(M18)할 수 있게 됨에 따라, 내용상 겹치거나 상충하는 다수의 활성 선호가 생길 리스크가 존재함. 시스템이 이를 감지하고 사용자에게 알리는 기제가 필요함 (정직성 원칙).
3.  **릴리스 병목**: 대규모 변경(40+ 커밋)이 누적되었으므로, 차기 마일스톤은 단순 기능 추가를 넘어 시스템 전반의 안정성을 확인하고 메인 브랜치로의 병합을 준비하는 "Consolidation" 성격을 띠어야 함.
4.  **M20 방향성**: "Personalization Scaling and Conflict Integrity"
    - 데이터 확장성을 확보하고(Scaling), 선호 간의 논리적 무결성을 검증하며(Conflict), 대규모 변경 세트를 안정화함(Integrity).

## 권고 사항 (RECOMMEND)
**RECOMMEND: implement M20 Axis 1 (SQLite Default and Scaling Migration)**

1.  **Configuration**:
    - `AppSettings`에서 `storage_backend`의 기본값을 `"sqlite"`로 전환 (기존 JSON은 하위 호환성을 위해 유지하되 명시적 설정 시에만 사용).
2.  **Migration Automation**:
    - 서버 시작 시 또는 전용 명령을 통해 8,000+ 개의 JSON 교정 레코드를 SQLite로 자동 이관하는 로직을 공고히 함.
    - `migrate_json_to_sqlite` 도구의 진행 상황을 `task_logger` 또는 UI 알림으로 노출.
3.  **Performance Verification**:
    - 8,000+ 레코드 환경에서 세션 로드 및 글로벌 후보 검색 속도가 200ms 이내임을 확인.
4.  **Validation**:
    - 대량 데이터 이관 후 데이터 손실 및 정합성 전수 검사 (단위 테스트).

**M20 전체 로드맵 계획**:
- **Axis 2 (Conflict)**: 활성 선호 간의 Statement 유사도/상충 감지 및 UI 경고 표시.
- **Axis 3 (Consolidation)**: 40+ 커밋 묶음에 대한 최종 릴리스 검증 및 PR #31 이후의 통합 완료.

## 기대 효과
- 수만 개의 교정 데이터도 지연 없이 처리하는 고성능 개인화 기반 확보.
- 파편화된 저장소 구조를 SQLite로 단일화하여 유지보수성 향상.
- 대규모 코드 변경 사항을 안정적으로 메인 브랜치에 통합할 준비 완료.
