# 2026-04-20 G-axis twelfth slice prioritization

## 개요
- seq 471(G5-unskip-thin-reader)을 통해 happy-path 상태 읽기 테스트가 복구됨.
- 현재 `TestRuntimeStatusRead`의 9개 테스트가 여전히 스킵 상태이며, 이들은 단순 읽기를 넘어선 "상태 전이 규칙(State Transition Rules)"의 구현을 요구함.
- G5의 unskipping 흐름을 가속화하기 위해, 오퍼레이터 개입 없이 코드 수준에서 가장 명확하게 정의할 수 있는 `STOPPING` -> `STOPPED` 전이 규칙을 구현하는 G5-unskip-STOPPING 슬라이스를 다음으로 선정함.

## 판단
1. **current-risk reduction (우선순위 1):**
   - 현재 시스템은 파일에 기록된 상태가 `STOPPING`이면 프로세스 생존 여부와 관계없이 그대로 보고함. 이는 프로세스가 이미 종료되었음에도 "중지 중"으로 표시되는 부정직한(untruthful) 상태임.
   - G5-unskip-STOPPING을 통해 프로세스 부재 시 `STOPPED`로 강제 전환함으로써 런타임 상태 보고의 정확성을 높임.

2. **implementation pattern establishment (우선순위 2):**
   - 이번 슬라이스는 `normalize_runtime_status` 내부에 외부 신호(supervisor liveness)를 주입하는 패턴을 정립함.
   - 이는 향후 `RUNNING` -> `BROKEN` 또는 `DEGRADED` 전이 로직을 구현할 때의 기반이 됨.

3. **기타 후보 검토:**
   - **G5-unskip-DEGRADED_REASON:** 단순 필드 정규화 작업이지만, 상태 전이의 핵심인 `runtime_state` 변경 로직을 먼저 잡는 것이 순서상 맞음.
   - **G5-unskip-AGED_AMBIGUOUS:** 시간 계산 로직이 포함되어 상대적으로 복잡하며, 단순 프로세스 생존 여부 확인(STOPPING)보다 위험도가 높음.
   - **G3, G7..G11:** 테스트 unskipping 사이클을 완결 지어 "Green" 궤도에 올리는 것이 현재 유지보수 축의 최우선 순위임.

## 권고 (RECOMMEND)
- **G5-unskip-STOPPING: STOPPING -> STOPPED transition implementation**
- 구체적 범위:
  - `pipeline_gui/backend.py` 수정:
    - `read_runtime_status(project: Path)` 시그니처는 유지하되, `normalize_runtime_status`가 supervisor 생존 여부를 알 수 있도록 인자를 추가하거나 내부에서 호출하도록 조정.
    - 권장 방식: `normalize_runtime_status(value: object | None, project: Path | None = None)`로 확장.
    - 규칙 추가: `if runtime_state == "STOPPING"` AND `project`가 주어졌으며 `_supervisor_pid(project)`가 `None`인 경우, `status["runtime_state"] = "STOPPED"`로 rewrite.
  - `tests/test_pipeline_gui_backend.py` 수정:
    - `test_read_runtime_status_converts_stopping_without_supervisor_into_stopped` (약 `:718`) 메서드 상단의 `@unittest.skip` 제거.
  - `python3 -m unittest tests/test_pipeline_gui_backend` 실행 결과 `OK (skipped=8)` 확인.

## 결론
G5-unskip-STOPPING을 통해 상태 전이 로직의 첫 조각을 구현하고, GUI 백엔드 테스트의 unskipping 사이클을 지속할 것을 추천함.
