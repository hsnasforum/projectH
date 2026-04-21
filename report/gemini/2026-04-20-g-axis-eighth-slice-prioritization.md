# 2026-04-20 G-axis eighth slice prioritization

## 개요
- seq 459(G6-sub1)를 통해 `SQLiteSessionStore`의 메서드 누락 및 `WebAppServiceTest`의 문구 불일치가 해결되어 28개의 테스트 실패가 해소됨.
- 현재 남은 주요 테스트 리스크는 `tests.test_pipeline_gui_backend`의 11건 실패(G5)와 `tests.test_web_app`의 10건 소켓 바인드 에러(G6-sub2)임.
- 시스템 안정성 확보를 위해 구현체와 테스트 간의 코드 드리프트(drift)가 명확한 G5를 다음 슬라이스로 선정함.

## 판단
1. **current-risk reduction (우선순위 1):**
   - `tests.test_pipeline_gui_backend::TestRuntimeStatusRead`의 실패는 `pipeline_gui/backend.py`와 테스트 모킹(mocking) 간의 속성(`_supervisor_pid`, `_pid_is_alive`) 불일치로 인한 `AttributeError`임.
   - 이는 GUI 백엔드의 상태 읽기 로직이 실제 구현과 동떨어져 있음을 의미하며, 11건의 실패를 해결함으로써 GUI 관리 기능의 신뢰성을 회복할 수 있음.

2. **환경 의존적 리스크(G6-sub2) 처리:**
   - `tests.test_web_app`의 residual 10건(`PermissionError`)은 샌드박스/환경의 소켓 바인드 권한 문제임.
   - 이를 해결하기 위해 복잡한 리팩터링(G6-sub2 Option ii)을 하거나 skip marker(Option i)를 넣는 것은 과도한 엔지니어링일 수 있음.
   - 현재로서는 이를 "환경 제약 사항"으로 정의하고, 코드 수준의 명확한 버그인 G5를 먼저 해결하는 것이 타당함.

3. **기타 후보 검토:**
   - **G11 (Adoption Meta-audit):** `SQLiteSessionStore`의 `staticmethod` 래핑 누락을 방지하기 위한 감사는 필요하지만, 당장 눈앞의 빨간색 테스트(G5)를 해결하는 것이 우선임.
   - **G3, G7..G10:** 지표 튜닝 및 어휘 정합성은 시스템이 "Green" 상태에 가까워진 후 진행하는 것이 프로젝트 관리상 안전함.

## 권고 (RECOMMEND)
- **G5: `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state truth-sync**
- 구체적 범위:
  - `pipeline_gui/backend.py` 및 `tests/test_pipeline_gui_backend.py` 대조.
  - `AttributeError`를 일으키는 `_supervisor_pid`, `_pid_is_alive` 등 누락되거나 이름이 바뀐 속성/메서드 동기화.
  - `python3 -m unittest tests/test_pipeline_gui_backend.py` 실행 결과 11건의 실패 해소 확인.

## 결론
G5를 통해 GUI 백엔드 테스트의 코드 드리프트를 해결하여 11건의 실패를 제거하고, 남은 소켓 바인드 에러는 환경 이슈로 분류하여 관리할 것을 추천함.
