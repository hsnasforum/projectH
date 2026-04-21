# 2026-04-20 G-axis ninth slice prioritization

## 개요
- seq 459(G6-sub1)를 통해 SQLite 저장소와 테스트 문구 정합성이 확보됨.
- 현재 GUI 백엔드 테스트(`tests.test_pipeline_gui_backend`)에서 11건의 대규모 실패(AttributeError 및 상태 불일치)가 지속되고 있음.
- 시스템 유지보수성과 GUI 관리 기능의 신뢰성 회복을 위해 G5를 다음 슬라이스로 선정함.

## 판단
1. **current-risk reduction (우선순위 1):**
   - `tests.test_pipeline_gui_backend::TestRuntimeStatusRead`의 실패는 `pipeline_gui/backend.py`의 구현(예: `supervisor_alive` 사용)과 테스트의 모킹(예: `_supervisor_pid` 패치 시도) 간의 인터페이스 불일치로 인한 `AttributeError`임.
   - 이는 GUI 백엔드 상태 관리 로직의 정직성(truthfulness)이 테스트 수준에서 깨져 있음을 의미하며, 이를 방치할 경우 GUI를 통한 런타임 상태 오판 리스크가 커짐.
   - G5를 통해 테스트와 구현체의 인터페이스를 동기화하고, 기대 상태(RUNNING, BROKEN, DEGRADED 등)에 대한 assertion을 현재 로직에 맞게 truth-sync함.

2. **환경 이슈(G6-sub2)와 기능 이슈(G5)의 분리:**
   - `tests.test_web_app`의 10건 `PermissionError`는 환경 특성상 발생하는 소켓 바인드 제한 문제임.
   - 이를 해결하기 위한 리팩터링보다는, 실제 코드 드리프트로 인한 실패인 G5를 해결하여 "순수 코드 결함"을 먼저 제거하는 것이 효율적임.

3. **기타 후보 검토:**
   - **G11 (Adoption Meta-audit):** 장기적인 예방 조치로 중요하지만, 현재 빨간색으로 표시되는 11개의 테스트 실패를 해결하는 것이 당장의 안정성 확보에 더 시급함.
   - **G3, G7..G10:** 내부 튜닝 및 어휘 정리 작업은 코어 시스템의 테스트가 안정화된 후 진행하는 것이 권장됨.

## 권고 (RECOMMEND)
- **G5: tests.test_pipeline_gui_backend::TestRuntimeStatusRead dirty-state truth-sync**
- 구체적 범위:
  - `pipeline_gui/backend.py` 내부의 상태 확인 헬퍼(`supervisor_alive`, `watcher_alive` 등)와 `tests/test_pipeline_gui_backend.py`의 모킹 대조 및 수정.
  - `AttributeError`를 유발하는 잘못된 패치 타겟(`_supervisor_pid` 등)을 실제 구현체 속성으로 교체.
  - `runtime_state` 판정 결과(RUNNING, BROKEN, DEGRADED, STOPPED)가 테스트 케이스의 의도와 일치하도록 truth-sync.
  - `python3 -m unittest tests/test_pipeline_gui_backend.py` 실행 시 `TestRuntimeStatusRead` 클래스의 모든 테스트 통과 확인.

## 결론
G5를 수행하여 GUI 백엔드 시스템의 테스트 부채를 청산하고, 런타임 상태 진단 로직의 신뢰성을 확보할 것을 추천함.
