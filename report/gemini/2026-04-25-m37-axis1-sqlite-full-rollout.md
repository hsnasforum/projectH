# 2026-04-25 M37-axis1-sqlite-full-rollout

## 결정: 후보 2 (Milestone 37 — SQLite Storage Default Rollout)

### 근거
1. **아키텍처 단순화 및 리스크 감소 (GEMINI.md 우선순위 1)**: Milestone 34~36을 통해 기능적 루프가 안정화되었으므로, 이제는 오랫동안 지연되었던 인프라 부채(JSON/SQLite 이중화)를 해결할 시점입니다. SQLite를 기본으로 확정하여 데이터 관리 효율성과 무결성을 높입니다.
2. **미결 과제 해소**: `TASK_BACKLOG`에 명시된 "Full migration and default rollout are deferred" 상태를 해소하여 프로젝트의 완성도를 높입니다. 이미 서비스 레벨에서 기능 동등성(Parity)이 충분히 검증되었습니다.
3. **가이드라인 준수**: `GEMINI.md`의 "same-family current-risk reduction" 원칙에 따라, 기능 추가보다 시스템의 근간이 되는 저장소 계층의 안정성을 먼저 확보합니다.

### 권고 Slice (M37 Axis 1)
- **목표**: 자동 마이그레이션 범위를 전체(Session, Preference, Artifact)로 확대하고 SQLite 기본 전환을 공식화.
- **실행 항목**:
    1. **마이그레이션 확대**: `app/web.py`의 `WebAppService.__init__`에서 `migrate_json_to_sqlite`를 호출할 때, 기존에 누락되었던 `sessions_dir`, `preferences_dir`, `artifacts_dir`를 모두 전달하여 기동 시 자동 전환이 완료되도록 수정합니다.
    2. **문서 동기화**: `docs/TASK_BACKLOG.md`에서 SQLite 관련 "deferred" 문구를 제거하고, 이를 "Current Product Identity"의 핵심 구성 요소로 업데이트합니다.
    3. **통합 검증**: `make e2e-test`를 실행하여 SQLite 환경에서 148개 시나리오 전수가 정상 동작함을 확인합니다.
- **검증**: 전체 E2E (148 scenarios) PASS 및 `tests/test_sqlite_store.py` PASS 확인.

### 후보 검토
- **후보 1 (Resume/Reject lifecycle)**: 가치 있는 개선이지만, 현재의 누적 데이터베이스 상태에서 발생할 수 있는 검증 불안정성(flakiness)을 고려할 때, 인프라 기반을 SQLite로 완전히 다진 후에 진행하는 것이 더 견고합니다.
- **후보 3 (유지보수)**: `watcher_core.*` re-export 정리 등은 구조 분리 phase의 마무리 성격이므로, 기능적/인프라적 마일스톤인 후보 2를 먼저 처리한 후 opportunistic하게 수행합니다.
