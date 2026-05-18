# 2026-04-25 M37-direction-infrastructure-rollout

## 결정: 후보 2 (Milestone 37 — SQLite Storage Default Rollout)

### 근거
1. **리스크 감소 (GEMINI.md 우선순위 1)**: Milestone 34~36을 통해 "Reviewed-Memory Loop"의 핵심 사용자 시나리오(가시성, 일시중지, 영속성)가 검증되었습니다. 이제는 `TASK_BACKLOG`에서 가장 오래된 숙원 과제이자 인프라 리스크인 "SQLite preference store 기본 전환"을 해결할 최적의 시기입니다.
2. **기술적 부채 상환**: 현재 프로젝트는 JSON과 SQLite 두 가지 백엔드를 병행 유지하는 부채를 안고 있습니다. 이미 서비스 레벨의 기능 동등성(Parity)이 27개 이상의 계약으로 확인된 상태이므로, 기본 설정을 전환하여 아키텍처를 단순화하고 데이터 무결성을 높여야 합니다.
3. **가이드라인 준수**: `GEMINI.md`의 "same-family current-risk reduction" 관점에서, Resume/Reject의 edge case 보강(후보 1)보다 시스템 전체의 저장소 안정성을 확보하는 인프라 강화가 장기적인 리스크 감소 효과가 더 큽니다.

### 권고 Milestone (M37) 및 Slice
- **Milestone 37**: Infrastructure Hardening & Backend Rollout
- **Axis 1 (M37)**: SQLite Storage Default Rollout
    - **목표**: `config/settings.py`에서 `storage_backend` 기본값을 `sqlite`로 변경하고, 기존 E2E 테스트가 SQLite 환경에서도 완벽히 통과함을 확인.
    - **실행 항목**:
        1. `config/settings.py`: `DEFAULT_STORAGE_BACKEND = "sqlite"`로 업데이트.
        2. `storage/sqlite_store.py`: `CorrectionStore`의 SQLite 구현체 및 마이그레이션 도구가 최신 스키마와 정합성을 이루는지 최종 점검.
        3. **Verification First**: `make e2e-test` (SQLite DB 환경)를 실행하여 148개 시나리오 전수 PASS 확인.
- **검증**: 전체 E2E (148 scenarios) 및 `tests/test_sqlite_store.py` PASS 확인.

### 후보 검토
- **후보 1 (Resume/Reject)**: 기능적 완결성 면에서 가치가 있으나, 현재의 누적 DB 환경에서 flakiness가 우려됩니다. 인프라 전환(SQLite) 이후, 필요 시 isolated test 환경과 함께 보강하는 것이 기술적으로 더 견고한 접근입니다.
- **후보 3 (유지보수)**: `watcher_core.*` re-export 정리 등은 상시 작업으로 수행 가능하므로, 명확한 마일스톤 목표인 후보 2를 우선합니다.
