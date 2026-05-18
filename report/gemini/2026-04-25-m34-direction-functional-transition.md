# 2026-04-25 M34-direction-functional-transition

## 결정: 후보 A (구조 phase 종료 → 기능 milestone 전환)

### 근거
1. **구조적 목표 달성 (GEMINI.md 우선순위 1)**: Milestone 30부터 33에 걸쳐 `watcher_core.py`의 4대 핵심 경계(Signals, Dispatch, State, Stabilizer)를 성공적으로 분리했습니다. 파일 크기가 5,001라인에서 3,977라인으로 감소했으며, 남은 11개 모듈 수준 함수(config/pane/prompt helpers)는 규모가 작고 핵심 루프와 밀접하게 연관되어 있어 추가 분리의 실익이 낮습니다.
2. **기술 부채의 균형**: Watcher 구조 개선이 충분히 진행되었으므로, 이제는 `TASK_BACKLOG`에 오래 머물러 있는 다른 인프라 부채인 "SQLite preference store 기본 전환"이나 기능적 강화로 초점을 옮길 시점입니다.
3. **병목 방지**: PR #33이 이미 6개 milestone(M28~M33)의 방대한 변경사항을 포함하고 있습니다. 여기서 구조적 "내부 정리"를 더 추가하는 것보다, 현재의 안정적인 구조 위에서 기능적 가치를 증명하는 것이 프로젝트의 리스크 관리 측면에서 유리합니다.

### 권고 Milestone (M34) 및 Slice
- **Milestone 34**: Infrastructure & Functional Hardening
- **Axis 1 (M34)**: SQLite preference store 기본 전환
    - **목표**: `config/settings.py`에서 `storage_backend` 기본값을 `sqlite`로 변경하고, 기존 JSON 데이터와의 호환성 및 마이그레이션 경로(필요 시)를 최종 확인.
    - **검증**: `make e2e-test` (SQLite config 기준 147 scenarios) 및 `tests/test_sqlite_store.py` 전수 PASS 확인.

### 후보 검토
- **후보 B (계속 구조 분리)**: `watcher_config.py` 추출은 아키텍처를 더 정교하게 만들 수 있으나, 현재 `watcher_core.py`의 위험도가 이미 크게 낮아진 상태에서 추가적인 mock patch 관리 비용을 발생시키는 것에 비해 가시적인 리스크 감소 효과가 적습니다.
- **문서화 필요**: M31~M33의 대규모 구조 변경 사항이 아직 `docs/MILESTONES.md`에 동기화되지 않았습니다. 차기 milestone 진행 과정에서 `doc-sync`를 통해 기록을 완결하는 것이 권장됩니다.
