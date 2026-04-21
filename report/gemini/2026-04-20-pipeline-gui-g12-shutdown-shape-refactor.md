# 2026-04-20 pipeline-gui-g12-shutdown-shape-refactor advisory

## 상황 요약
- `G5-unskip-DEGRADED` 패밀리가 seq 501에서 완전히 닫혔습니다.
- `pipeline_gui/backend.py`의 `normalize_runtime_status` 내 `DEGRADED` 분기가 18줄의 guard와 5줄의 ternary body를 가진 복잡한 형태로 성장했습니다.
- 현재 `supervisor_missing`으로 유도되는 4개 분기(STOPPING, BROKEN, DEGRADED, RUNNING→BROKEN)가 동일한 7개 필드(`runtime_state`, `degraded_reason/s`, `control`, `active_round`, `watcher`, `lanes`)를 중복해서 재작성하고 있습니다.

## 판단
- **G12 `_apply_shutdown_shape` refactor**를 다음 슬라이스로 권고합니다.
- **이유**: `DEGRADED` 분기의 가독성과 유지보수성이 한계점에 도달했으며, 특히 `lanes` 리스트 컴프리헨션을 포함한 shutdown 리셋 로직이 여러 곳에 흩어져 있어 regression surface가 넓습니다. 이를 공통 헬퍼로 통합함으로써 향후 `DEGRADED` 조건이나 다른 상태 전이를 추가할 때 발생할 수 있는 오동작 위험을 낮출 수 있습니다.
- **우선순위**: `GEMINI.md`의 "same-family current-risk reduction" 기준에 부합합니다.

## 권고 세부사항 (G12)
- **대상 파일**: `pipeline_gui/backend.py`
- **핵심 변경**:
  - `_apply_supervisor_missing_status(status, target_state, reason, shutdown=True)` 프라이빗 헬퍼 도입.
  - `shutdown=True`일 때 `control`, `active_round`, `watcher`, `lanes` 필드를 "none/stopped" 상태로 일제히 리셋하는 "shutdown shape"를 구현.
  - `DEGRADED` 분기는 `shutdown=False`로 호출하여 필드 보존 규칙을 유지.
  - STOPPING, BROKEN, RUNNING→BROKEN 분기는 `shutdown=True`로 호출하여 중복 코드 제거.
- **검증**:
  - `tests.test_pipeline_gui_backend`의 모든 45개 테스트(특히 10개 이상의 `supervisor_missing` 관련 green cells)가 그대로 green을 유지해야 함.
  - `tests.test_smoke` baseline (11/27/7/6 OK) 유지 확인.

## 대안 검토
- **G7 REASON_CODE**: 구조적으로 중요하나, 현재 코드의 복잡도가 증가한 `backend.py` 내부 정리가 더 시급한 risk reduction이라고 판단함.
- **G8 memory-foundation**: 새로운 품질 축으로의 전환은 이 내부 cleanup 이후에 진행하는 것이 더 안정적임.
