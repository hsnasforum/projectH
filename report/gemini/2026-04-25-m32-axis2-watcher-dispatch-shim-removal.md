# 2026-04-25 M32-axis2-watcher-dispatch-shim-removal

## 결정: 후보 A (M32 Axis 2 — _watcher_core_compat shim 제거)

### 근거
1. **아키텍처 정합성 (GEMINI.md 우선순위 1)**: `watcher_dispatch.py`가 `sys.modules`를 통해 `watcher_core`를 동적으로 조회하는 현재의 shim 구조는 모듈 간의 암시적 결합을 만듭니다. 이는 `watcher_core.py`를 더 작은 단위로 쪼개는 향후 작업에 걸림돌이 될 수 있으므로, 분리 직후에 이를 명시적인 의존성으로 전환하는 것이 리스크 감소 측면에서 최우선입니다.
2. **기술 부채 조기 상환**: M32 Axis 1에서 임시로 도입된 호환성 계층을 제거하여 신규 모듈(`watcher_dispatch.py`)을 완전히 자립적인 상태로 만듭니다.
3. **가이드라인 준수**: `GEMINI.md`의 tie-break 기준인 "same-family current-risk reduction"을 따릅니다. Watcher family의 구조 개선 작업을 완결성 있게 마무리합니다.

### 권고 Slice (M32 Axis 2)
- **목표**: `watcher_dispatch.py`에서 `_watcher_core_compat` shim 및 관련 thin wrapper 7개를 제거하고, 테스트 코드를 갱신하여 직접적인 mock patch를 사용하도록 변경.
- **실행 항목**:
    - `watcher_dispatch.py`: `_watcher_core_compat` 함수 및 7개 wrapper(`_capture_pane_text` 등) 삭제. 내부 호출은 `pipeline_runtime.lane_surface`에서 직접 가져온 `_shared_*` 함수를 사용하도록 수정.
    - `tests/test_watcher_core.py`: dispatch 경로를 타는 테스트 케이스(예: `CodexDispatchConfirmationTest`)에서 `mock.patch("watcher_core._shared_*")` 대신 `mock.patch("watcher_dispatch._shared_*")`를 사용하도록 업데이트.
- **검증**:
    - `watcher_core.py`, `watcher_dispatch.py`, `watcher_signals.py`의 상호작용 하에 전체 216개 unit tests가 PASS함을 확인.

### 후보 검토
- **후보 B (기능 milestone 전환)**: 기능 전환도 가치가 있으나, 현재 진행 중인 Watcher 구조 개선 작업에서 "깨진 유리창"과 같은 shim을 남겨두는 것은 향후 분리 작업의 난이도를 높이는 리스크가 있습니다. 구조적 안정성을 먼저 확보한 후 기능을 추가하는 것이 프로젝트의 "North Star"에 부합합니다.
