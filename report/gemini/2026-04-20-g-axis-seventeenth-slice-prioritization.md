# 2026-04-20 G-axis seventeenth slice prioritization

## 개요
- seq 486(G5-unskip-AGED_AMBIGUOUS_BARE)을 통해 추가 구현 없이 통과 가능한 테스트 1건이 복구됨.
- 현재 `TestRuntimeStatusRead` 클래스에 4개의 테스트가 스킵 상태로 남아 있음.
- 이 중 `recent_field_quiescent_running_status_broken_without_pids`는 현재의 일괄적인 `state="BROKEN"` 덮어쓰기 로직으로 인해 `AssertionError: 'BROKEN' != 'OFF'` 실패가 예상됨.
- 레인(lane)의 정지 상태를 존중하도록 정규화 로직을 개선하고 해당 테스트를 복구하는 G5-unskip-QUIESCENT-LANE 슬라이스를 선정함.

## 판단
1. **current-risk reduction (우선순위 1):**
   - 현재 시스템은 감시자가 없을 경우 모든 레인의 상태를 `BROKEN`으로 강제 전환함. 하지만 이미 의도적으로 정지(`OFF`)된 레인은 그 상태를 유지하면서 비정상 종료 노트만 추가하는 것이 더 정직한(truthful) 보고임.
   - G5-unskip-QUIESCENT-LANE을 통해 이 "과잉 정규화" 문제를 해결하고 진단 정보의 정밀도를 높임.

2. **same-family incremental progress (우선순위 2):**
   - 복잡한 시간 축 로직(age machinery)을 도입하기 전에, 현재의 상태 전이 패턴 내에서 가장 명확하게 해결 가능한 "레인 상태 보존" 규칙을 먼저 구현함.
   - 이는 향후 `DEGRADED` 계열 테스트를 다룰 때 레인 상태를 어떻게 처리할지에 대한 가이드라인이 됨.

3. **기타 후보 검토:**
   - **G5-unskip (나머지):** `DEGRADED` 계열은 시간 축 로직과의 충돌 문제로 인해 이번 "레인 상태 보존" 규칙이 먼저 확립된 후 다루는 것이 안전함.
   - **G12 (Shared Helper):** 현재 분기가 3개이므로 리팩터링의 실익이 크지 않음. 4번째 분기(`DEGRADED`) 추가 시점에 통합 검토함.
   - **G3, G7..G11:** 테스트 unskipping 사이클을 유지함.

## 권고 (RECOMMEND)
- **G5-unskip-QUIESCENT-LANE: preserve quiescent lane state in BROKEN normalization**
- 구체적 범위:
  - `pipeline_gui/backend.py` 수정:
    - `normalize_runtime_status` 내부의 두 `BROKEN` 관련 분기(`:128`, `:151` 인근) 수정.
    - 레인 상태 할당 로직 변경: `"state": lane.get("state") if str(lane.get("state") or "") == "OFF" else "BROKEN"`
  - `tests/test_pipeline_gui_backend.py` 수정:
    - `test_read_runtime_status_marks_recent_field_quiescent_running_status_broken_without_pids` (약 `:942`) 메서드 상단의 `@unittest.skip` 제거.
  - `python3 -m unittest tests/test_pipeline_gui_backend` 실행 결과 `OK (skipped=3)` 확인.

## 결론
G5-unskip-QUIESCENT-LANE을 통해 레인 상태 정규화 로직을 정교화하고, 스킵된 테스트 카운트를 3개로 줄일 것을 추천함.
