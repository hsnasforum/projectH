# 2026-04-20 G-axis fourteenth slice prioritization

## 개요
- seq 477(G5-unskip-DEGRADED_REASON)을 통해 `BROKEN` 상태일 때의 감시자(supervisor) 부재 정규화가 완료됨.
- 현재 `TestRuntimeStatusRead` 클래스에 7개의 테스트가 스킵 상태로 남아 있음.
- 이 중 `RUNNING` 상태로 기록되어 있으나 실제 감시자 프로세스가 죽은 "좀비 상태"를 탐지하고 `BROKEN`으로 전환하는 핵심 규칙을 구현하기 위해 G5-unskip-RUNNING_TO_BROKEN 슬라이스를 선정함.

## 판단
1. **current-risk reduction (우선순위 1):**
   - 시스템이 `RUNNING`으로 표시되고 있지만 실제로는 감시자가 없는 상태는 사용자에게 가장 큰 혼란을 주는 "거짓 양성(false positive)" 리스크임.
   - 이를 `BROKEN`으로 정확히 보고하게 함으로써 시스템의 상태 정직성(truthfulness)을 핵심 경로에서 확보함.

2. **Detection Logic Widen (필수 선결 과제):**
   - 현재 `normalize_runtime_status`는 `_supervisor_pid(project) is None`으로만 감시자 부재를 판단함. 이는 PID 파일이 없는 경우만 해당하며, 프로세스가 죽었으나 PID 파일이 남은 경우는 놓치게 됨.
   - 이번 슬라이스에서 `supervisor_alive(project)[0]`를 사용하도록 판단 로직을 확장하여 실질적인 프로세스 생존 여부를 반영함.

3. **기타 후보 검토:**
   - **G5-unskip-AGED_AMBIGUOUS:** 여전히 시간 계산 및 모호성 판단 로직이 복잡하여, 좀비 프로세스 탐지(RUNNING -> BROKEN)라는 더 명확한 리스크 해결을 우선함.
   - **G7..G11:** 핵심 상태 머신 테스트가 순차적으로 "Green"으로 복구되는 흐름을 유지하는 것이 현재 프로젝트의 안정성 확보에 가장 기여도가 높음.

## 권고 (RECOMMEND)
- **G5-unskip-RUNNING_TO_BROKEN: RUNNING -> BROKEN zombie process detection**
- 구체적 범위:
  - `pipeline_gui/backend.py` 수정:
    - `normalize_runtime_status` 내부의 `supervisor_missing` 정의 수정: `supervisor_missing = project is not None and not supervisor_alive(project)[0]`
    - 신규 분기 추가: `if supervisor_missing and runtime_state == "RUNNING"` 인 경우, `runtime_state`를 `"BROKEN"`으로 변경하고 `degraded_reason` 및 lane 정보를 `supervisor_missing` 형태(seq 477 패턴)로 정규화한 후 반환.
  - `tests/test_pipeline_gui_backend.py` 수정:
    - `test_read_runtime_status_marks_stale_running_status_broken_when_supervisor_is_missing` (약 `:643`) 메서드 상단의 `@unittest.skip` 제거.
  - `python3 -m unittest tests/test_pipeline_gui_backend` 실행 결과 `OK (skipped=6)` 확인.

## 결론
G5-unskip-RUNNING_TO_BROKEN을 통해 감시자 프로세스 생존 여부에 기반한 실질적인 상태 전이 로직을 완성하고, 런타임 진단 시스템의 핵심 리스크를 해소할 것을 추천함.
