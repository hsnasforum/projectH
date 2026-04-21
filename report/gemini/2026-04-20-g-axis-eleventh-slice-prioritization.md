# 2026-04-20 G-axis eleventh slice prioritization

## 개요
- seq 468(G5-unskip-A)에서 `_supervisor_pid` 및 `_pid_is_alive` 헬퍼가 구현되고 1개의 테스트가 unskip됨.
- 현재 `TestRuntimeStatusRead` 클래스에 10개의 테스트가 스킵 상태로 남아 있음.
- 점진적인 unskipping 사이클을 지속하기 위해, 현재의 thin-reader 구현만으로도 통과 가능한 `test_read_runtime_status_from_current_run_pointer`를 다음 슬라이스로 선정함.

## 판단
1. **current-risk reduction (우선순위 1):**
   - 현재 스킵된 테스트들은 런타임 상태 관리 로직의 정직성을 검증하지 못함.
   - G5-unskip-B는 이미 지원되는 기능을 검증하는 테스트를 활성화하여, "스킵된 테스트"라는 잠재적 리스크를 줄임.

2. **same-family incremental progress (우선순위 2):**
   - 헬퍼 구현 이후, 복잡한 상태 전이 로직 없이도 통과 가능한 가장 좁은(bounded) 슬라이스임.
   - 이 테스트는 `read_runtime_status`가 `current_run.json` 포인터를 따라 `status.json`을 정확히 읽어오는지 확인하는 핵심적인 "기본 경로(happy path)" 검증임.

3. **기타 후보 검토:**
   - **G5-unskip (나머지):** 다른 9개의 테스트는 `read_runtime_status` 내부에 상태 전이(RUNNING→BROKEN 등) 로직을 추가로 구현해야 통과할 수 있으므로, 이번 라운드의 "가장 작은coherent slice" 원칙에 따라 후순위로 미룸.
   - **G3, G7..G11:** 테스트 안정화 흐름을 끊지 않고 지속하는 것이 현재 유지보수 축의 우선순위에 부합함.

## 권고 (RECOMMEND)
- **G5-unskip-B: unskip test_read_runtime_status_from_current_run_pointer**
- 구체적 범위:
  - `tests/test_pipeline_gui_backend.py` 수정:
    - `test_read_runtime_status_from_current_run_pointer` (약 `:594`) 메서드 상단의 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` 데코레이터 제거.
  - `python3 -m unittest tests/test_pipeline_gui_backend` 실행 결과 `OK (skipped=9)` 확인.

## 결론
G5-unskip-B를 통해 핵심적인 상태 읽기 기본 경로 테스트를 활성화하고, 점진적인 unskipping 사이클을 이어갈 것을 추천함.
