# 2026-04-20 G-axis fifteenth slice prioritization

## 개요
- seq 480(G5-unskip-RUNNING_TO_BROKEN)을 통해 실질적인 감시자(supervisor) 생존 여부 확인 로직과 `RUNNING` -> `BROKEN` 전이 규칙이 구현됨.
- 현재 `TestRuntimeStatusRead` 클래스에 6개의 테스트가 스킵 상태로 남아 있음.
- 이 중 `test_read_runtime_status_marks_recent_quiescent_running_status_broken_without_supervisor`는 seq 480의 "좀비 탐지" 규칙으로 이미 통과 가능한 상태임을 확인하였으므로, 별도의 코드 수정 없이 이를 unskip하는 슬라이스를 선정함.

## 판단
1. **current-risk reduction (우선순위 1):**
   - 이미 구현된 로직으로 검증 가능한 테스트를 활성화하여, "이미 해결된 리스크"가 스킵된 상태로 방치되는 것을 방지함.
   - G5-unskip-B를 통해 unskip 사이클의 속도를 높이고 테스트 가용 범위를 확장함.

2. **zero-cost implementation (우선순위 2):**
   - `pipeline_gui/backend.py`의 수정이 전혀 필요하지 않으며, 오직 데코레이터 삭제만으로 한 개의 red cell을 green으로 전환할 수 있는 가장 효율적인 슬라이스임.

3. **기타 후보 검토:**
   - **G5-unskip (나머지):** `DEGRADED` 계열 테스트(1015, 1199, 1261)는 현재의 blanket `RUNNING -> BROKEN` 규칙과 충돌하므로, 더 정교한 상위 규칙(upper rule) 구현이 선행되어야 함.
   - **G3, G7..G11:** 테스트 unskipping 사이클을 완결 짓는 흐름을 유지함.

## 권고 (RECOMMEND)
- **G5-unskip-B: unskip recent quiescent RUNNING -> BROKEN test**
- 구체적 범위:
  - `tests/test_pipeline_gui_backend.py` 수정:
    - `test_read_runtime_status_marks_recent_quiescent_running_status_broken_without_supervisor` (약 `:866`) 메서드 상단의 `@unittest.skip` 제거.
  - `python3 -m unittest tests/test_pipeline_gui_backend` 실행 결과 `OK (skipped=5)` 확인.

## 결론
G5-unskip-B를 통해 이미 구현된 좀비 탐지 로직의 유효성을 추가로 검증하고, 스킵된 테스트 카운트를 5개로 줄일 것을 추천함.
