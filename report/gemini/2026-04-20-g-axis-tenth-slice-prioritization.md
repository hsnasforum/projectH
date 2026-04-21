# 2026-04-20 G-axis tenth slice prioritization

## 개요
- seq 465(G5-sub-D)를 통해 GUI 백엔드 테스트의 drifted cell들이 투명하게 defer(skip) 처리됨.
- 현재 `TestRuntimeStatusRead`의 11개 테스트가 스킵 상태이며, 이 중 일부는 구현체(`pipeline_gui/backend.py`)에 테스트가 기대하는 내부 헬퍼(`_supervisor_pid`, `_pid_is_alive`)가 없어 패치 시 `AttributeError`가 발생하는 상태임.
- G5의 지연(deferral) 상태를 점진적으로 해소하기 위해, 필수 헬퍼 구현 및 최소 단위의 테스트 복구를 수행하는 G5-unskip-A를 다음 슬라이스로 선정함.

## 판단
1. **current-risk reduction (우선순위 1):**
   - 현재 11개의 테스트가 스킵되어 있어 실제 런타임 상태 진단 로직의 변경 사항을 검증할 수 없는 리스크가 있음.
   - G5-unskip-A는 테스트가 의존하는 최소 인터페이스를 구현하여, "인터페이스 부재"로 인한 에러 리스크를 제거함.

2. **same-family incremental progress (우선순위 2):**
   - G5-sub-D로 만든 "투명한 지연" 상태에서 한 걸음 나아가, 실제 구현을 채워넣기 시작하는 자연스러운 후속 단계임.
   - 모든 테스트를 한 번에 unskip하는 대신, 순수하게 `AttributeError`만으로 막혀 있던 테스트 1건(`test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive`)을 타겟으로 삼아 범위를 엄격히 제한함.

3. **기타 후보 검토:**
   - **G11 (Adoption Audit):** 중요하지만 G5의 unskipping 흐름을 시작하는 것이 현재 "Maintenance" 축의 우선순위에 더 부합함.
   - **G7 (Vocabulary):** 어휘 정합성 이전에 핵심 로직의 테스트 가용성(unskipping)이 확보되어야 함.
   - **G3, G8..G10:** 내부 튜닝 및 정리 작업은 테스트 안정화 이후로 후순위 유지.

## 권고 (RECOMMEND)
- **G5-unskip-A: implement _supervisor_pid + _pid_is_alive helpers**
- 구체적 범위:
  - `pipeline_gui/backend.py` 수정:
    - `_supervisor_pid(project: Path) -> int | None` 구현 (기존 `supervisor_alive` 로직 이관).
    - `_pid_is_alive(pid: int) -> bool` 구현 (기존 `os.kill(pid, 0)` 등 로직 이관).
    - `supervisor_alive(project: Path) -> tuple[bool, int | None]`가 위 두 헬퍼를 사용하도록 리팩터링.
  - `tests/test_pipeline_gui_backend.py` 수정:
    - `test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive` (약 `:1136`) 메서드 상단의 `@unittest.skip` 데코레이터 제거.
  - `python3 -m unittest tests/test_pipeline_gui_backend` 실행 결과 `OK (skipped=10)` 확인.

## 결론
G5-unskip-A를 통해 GUI 백엔드 테스트의 인터페이스 불일치를 해결하고, 점진적인 unskipping 사이클을 시작하여 시스템 안정성을 강화할 것을 추천함.
