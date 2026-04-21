# 2026-04-20 G-axis sixteenth slice prioritization

## 개요
- seq 483(G5-unskip-RECENT_QUIESCENT_BARE)을 통해 추가 구현 없이 통과 가능한 테스트 1건이 복구됨.
- 현재 `TestRuntimeStatusRead` 클래스에 5개의 테스트가 스킵 상태이며, 이들은 스냅샷의 시간(age)에 따른 상태 전이(`RUNNING` -> `BROKEN` vs `DEGRADED`)를 요구함.
- 상태 전이 로직의 시간 축(Time-axis) 구현을 위해, 오래된 스냅샷을 `BROKEN`으로 처리하는 G5-unskip-AGED_AMBIGUOUS 슬라이스를 다음으로 선정함.

## 판단
1. **current-risk reduction (우선순위 1):**
   - 현재 시스템은 스냅샷이 아무리 오래되어도 감시자가 없으면 일관된 전이 규칙이 없음.
   - G5-unskip-AGED_AMBIGUOUS를 통해 15초 이상의 오래된 스냅샷을 명확히 `BROKEN`으로 판정함으로써, "최신성"에 기반한 상태 진단의 정직성을 확보함.

2. **foundation for DEGRADED family (우선순위 2):**
   - 이번 슬라이스에서 구현할 "스냅샷 나이 계산" 로직은 남은 `DEGRADED` 계열 테스트(최근 활동 시 `DEGRADED` 보고)를 해결하기 위한 필수 기반 작업임.
   - 15초 임계값을 도입하여 `BROKEN`(stale)과 `DEGRADED`(recent)를 구분하는 로직 패턴을 확립함.

3. **기타 후보 검토:**
   - **G5-unskip (나머지):** `DEGRADED` 계열은 이번 시간 축 로직이 선행되어야 unskip 가능함.
   - **G3, G7..G12:** 테스트 안정화 사이클을 완결 짓는 흐름을 유지함.

## 권고 (RECOMMEND)
- **G5-unskip-AGED_AMBIGUOUS: aged ambiguous snapshot to BROKEN transition**
- 구체적 범위:
  - `pipeline_gui/backend.py` 수정:
    - `from pipeline_runtime.schema import parse_iso_utc` 임포트 추가.
    - `SNAPSHOT_STALE_THRESHOLD = 15.0` 정의.
    - `normalize_runtime_status` 내부에 스냅샷 나이(`snapshot_age`) 계산 로직 추가.
    - `RUNNING -> BROKEN` 분기(seq 480 추가분)를 수정하여, `snapshot_age > 15.0`일 때만 `BROKEN`으로 전이하고, 그 외(recent 또는 undated)는 `DEGRADED` 및 전용 사유(`supervisor_missing_recent_ambiguous`)를 반환하도록 함.
  - `tests/test_pipeline_gui_backend.py` 수정:
    - `test_read_runtime_status_converts_aged_ambiguous_snapshot_into_broken` (약 `:1062`) 메서드 상단의 `@unittest.skip` 제거.
  - `python3 -m unittest tests/test_pipeline_gui_backend` 실행 결과 `OK (skipped=4)` 확인.

## 결론
G5-unskip-AGED_AMBIGUOUS를 통해 상태 전이 로직에 시간 차원을 도입하고, 점진적인 unskipping 사이클을 고도화할 것을 추천함.
