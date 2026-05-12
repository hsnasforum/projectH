# 2026-04-25 M33-axis2-watcher-decomposition-stabilizer

## 결정: 후보 A (M33 Axis 2 — StabilizeSnapshot/ArtifactStabilizer 추출)

### 근거
1. **구조적 응집도 향상 (GEMINI.md 우선순위 1)**: `watcher_core.py`에 남아 있는 아티팩트 안정화(Stabilization) 로직은 파일 시스템 상태와 체크섬을 다루는 독립적인 책임 영역입니다. 이를 `watcher_state.py`로 이동함으로써 `watcher_core.py`를 순수한 제어 루프(Loop Engine)로 정제하는 작업을 지속합니다.
2. **모듈 결합도 최적화**: `ArtifactStabilizer`는 `WatcherCore` 클래스 내부에서 초기화되어 사용되지만, 그 정의 자체는 독립적인 유틸리티 성격이 강합니다. 이미 존재하는 `watcher_state.py`에 이를 통합하여 관련 데이터 모델과 행위를 한곳으로 모읍니다.
3. **가이드라인 준수**: `GEMINI.md`의 tie-break 기준인 "same-family current-risk reduction"을 따릅니다. 4,000라인 수준인 `watcher_core.py`를 더 작고 관리 가능한 단위로 계속 쪼개 나가는 것이 장기적인 유지보수 리스크 감소에 기여합니다.

### 권고 Slice (M33 Axis 2)
- **목표**: `watcher_core.py`에서 아티팩트 안정화 관련 클래스와 헬퍼를 `watcher_state.py`로 이동.
- **대상 클래스/함수**:
    - `compute_file_sha256` (함수)
    - `StabilizeSnapshot` (클래스)
    - `ArtifactStabilizer` (클래스)
- **실행 항목**:
    - `watcher_state.py`: 대상 클래스/함수 추가 및 필요한 import (`hashlib` 등) 보강.
    - `watcher_core.py`: 대상 삭제 및 `watcher_state`에서 import하여 re-export 계약 유지.
- **검증**:
    - `watcher_core.py`, `watcher_state.py` 컴파일 및 전체 216개 unit tests PASS 확인.

### 후보 검토
- **후보 B (기능 전환)**: 기능 전환도 고려할 수 있으나, Watcher 구조 개선 작업에서 "Stabilization"이라는 명확한 경계를 먼저 정리하는 것이 향후 `WatcherCore` 클래스 자체의 리팩토링이나 기능 추가 시 간섭을 줄이는 길입니다.
