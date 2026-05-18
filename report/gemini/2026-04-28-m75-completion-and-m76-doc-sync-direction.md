# Advisory Log: 2026-04-28 — M75 완료 및 M76 데이터 계층 안정화 마감(Truth-Sync) 권고

## 개요
M75 Axis 1을 통해 비대해진 `storage/sqlite_store.py`를 책임별 하위 모듈(`storage/sqlite/`)로 분리하는 구조 개선 작업이 완료되었습니다. 이로써 M72–M74의 물리 검증(Physical Validation)과 M75의 구조 분해(Structural Decomposition)가 결합되어 데이터 계층의 인프라 정합성이 "v1.5 structural" 단계의 목표 수준에 도달했습니다. 본 advisory는 마일스톤과 백로그를 최신화하고 구조 개선 단계를 공식 마무리하기 위한 M76 Truth-Sync를 권고합니다.

## 분석 및 상태 확인
- **M75 성과**: 1,100라인의 모놀리식 스토어 파일을 8개의 전문 모듈로 분리하여 유지보수성을 극대화했습니다. 기존 129개의 단위 테스트가 수정 없이 통과되어 하위 호환성도 검증되었습니다. (verify CONTROL_SEQ 1269)
- **인프라 상태**:
  - **정합성**: Correction, Preference, Artifact, TaskLog 전반에 읽기 경로 물리 검증 도입 완료 (M72–M74).
  - **구조**: Handler 계층(M70) 및 Store 계층(M75)의 구조 분해 완료.
- **문서 격차**: M71에서 M70까지 동기화했으나, 이후 급격히 진행된 M72–M75(검증 시리즈 + SQLite 분해)의 성과가 아직 `MILESTONES.md` 및 `TASK_BACKLOG.md`에 반영되지 않았습니다.

## 권고 사항
`RECOMMEND: doc-sync M76 Structural Hardening Phase Finish & Truth-Sync`

### 권고 근거
1. **진실 정합성 (Truth-Sync)**: M72–M75의 성과를 공식 기록하여 "v1.5 structural" 단계가 의도한 "데이터 및 구조 안정화" 목표를 달성했음을 확정합니다. (Priority 1: same-family risk reduction)
2. **Phase 전환 준비**: 구조적 부채가 상당 부분 해소됨에 따라, 다음 마일스톤(M77+)부터는 신규 기능 Axis(예: 선호도 주입 신뢰도 또는 모델 성능 최적화)로 안전하게 전환할 수 있는 베이스라인을 제공합니다.
3. **백로그 정산**: `TASK_BACKLOG.md`에서 오랫동안 미완으로 남아있던 "physical validation remains" 항목을 "DONE"으로 전환하여 운영자의 판단 부하를 줄입니다.

### M76 상세 가이드
- **MILESTONES.md**: M72 (Correction Validation) ~ M75 (SQLite Decomp) 완료 기록 추가 및 "Structural Hardening" Axis로 그룹화.
- **TASK_BACKLOG.md**:
  - "Not Implemented" 3번 항목(Correction-memory schema)을 "DONE"으로 업데이트.
  - "Already Implemented" 섹션에 물리 검증 및 SQLite 구조 분해 성과 반영.
- **Next Priorities**: M77부터 시작할 새로운 기능 Axis 또는 다음 구조적 타겟(예: `ChatHandlerMixin` 분리)에 대한 의사결정 포함.

## 결론
데이터 계층의 물리적·구조적 Hardening이 완료된 현재 시점에서, M76 Doc-Sync를 통해 "v1.5 structural" 단계를 성공적으로 마무리하고 다음 단계로의 도약을 준비할 것을 권고합니다.
