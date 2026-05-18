# 2026-04-25 M33-direction-watcher-decomposition-state

## 결정: 후보 A (M33 Axis 1 — watcher_core.py 추가 구조 분리)

### 근거
1. **구조적 명확성 확보 (GEMINI.md 우선순위 1)**: `watcher_core.py`의 핵심 클래스인 `WatcherCore`가 비대해진 원인 중 하나는 오케스트레이션과 좌표 데이터 모델(Coordination State)이 섞여 있기 때문입니다. `Lease`, `ControlSignal` 등 핵심 상태 클래스를 분리함으로써 파일 크기를 줄이고 데이터 모델의 소유권을 명확히 합니다.
2. **기술적 부채 해결**: M30(Signals), M32(Dispatch)에 이어 "Coordination State"를 분리하는 것은 `WatcherCore`를 순수한 "제어 루프(Loop Engine)"로 정제하는 전략적 수순입니다.
3. **가이드라인 준수**: `GEMINI.md`의 tie-break 기준인 "same-family current-risk reduction"을 따릅니다. 4,387라인의 거대 파일 리스크를 지속적으로 줄여 나갑니다.

### 권고 Slice (M33 Axis 1)
- **목표**: `watcher_core.py`에서 코디네이션 상태 및 임대 관리 클래스를 `watcher_state.py`로 분리.
- **대상 클래스/함수**:
    - `WatcherTurnState` (Enum)
    - `LeaseData`, `ControlSignal`, `PaneLease`, `DedupeGuard` (Classes)
    - `ManifestCollector` (Class) — 선택적 포함 가능
- **검증**:
    - `watcher_core.py`가 새 모듈에서 상태 클래스를 가져오도록 수정.
    - 기존 216개 unit tests (Core/Signals/Monitor/Monitor) 통과 및 `mock.patch` 경로 정합성 확인.

### 후보 검토
- **후보 B (기능 전환)**: M31에서 E2E 검증이 성공적으로 완료되었으므로, 현재의 구조 개선 흐름을 끊지 않고 파일 크기를 안정권(예: 3,000라인 이하)으로 줄이는 것이 우선입니다.
- **후보 C (PR #33)**: Operator 결정 대기 중에도 로컬 구조 개선은 독립적으로 진행 가능하며, 구조 개선 결과물은 PR #33의 가치를 더욱 높입니다.
