# 2026-04-20 G-axis eighteenth slice prioritization

## 개요
- seq 489(G5-unskip-QUIESCENT_LANE)를 통해 레인 정지 상태 보존 로직이 구현되고 1개의 테스트가 unskip됨.
- 현재 `TestRuntimeStatusRead` 클래스에 3개의 테스트가 스킵 상태로 남아 있으며, 이들은 모두 `DEGRADED` 상태 전이(최근 활동 또는 날짜 미기입 스냅샷)를 요구함.
- G5의 마지막 조각들을 해결하고 GUI 백엔드 테스트를 완전히 "Green"(또는 환경 제약 제외 Green)으로 만들기 위해 G5-unskip-DEGRADED-FAMILY 슬라이스를 선정함.

## 판단
1. **current-risk reduction (우선순위 1):**
   - 현재 3개의 `DEGRADED` 계열 테스트가 스킵되어 있어, 감시자 부재 시의 "일시적 모호함"을 처리하는 로직의 정직성을 검증할 수 없음.
   - G5-unskip-DEGRADED-FAMILY를 통해 이 마지막 3개 셀을 한 번에 해결함으로써 G5 가족(Family)을 완결함.

2. **time-axis implementation (필수):**
   - 이전 라운드(seq 486)에서 전체적인 시간 기반 전이는 거절되었으나, 남은 3개 테스트는 명확히 시간(최근 15초 이내) 또는 날짜 부재 시 `DEGRADED`를 요구하고 있음.
   - 이번 슬라이스에서 `SNAPSHOT_STALE_THRESHOLD`를 도입하고, `has_active_surface`(활성 레인 또는 감시자 생존 신호) 신호를 결합하여 정밀한 `DEGRADED` 전이 규칙을 구현함.

3. **기타 후보 검토:**
   - **G3, G7..G11:** 핵심 진단 로직의 테스트 unskipping 사이클을 완결 짓는 것이 현재 유지보수 축의 최우선 순위임.
   - **G12 (Refactor):** 4번째 상태 전이 분기(`DEGRADED`)가 추가되면 코드 중복이 임계치에 도달하므로, 이번 슬라이스 구현 후 또는 구현 과정에서 자연스럽게 검토 가능함.

## 권고 (RECOMMEND)
- **G5-unskip-DEGRADED-FAMILY: implement DEGRADED transition for recent/undated snapshots**
- 구체적 범위:
  - `pipeline_gui/backend.py` 수정:
    - `from pipeline_runtime.schema import parse_iso_utc` 임포트 추가.
    - `SNAPSHOT_STALE_THRESHOLD = 15.0` 상수 추가.
    - `normalize_runtime_status` 내부에 `snapshot_age` 계산 및 `has_active_surface` 판정 로직 추가.
    - `RUNNING -> BROKEN` 분기 앞에 **신규 DEGRADED 분기** 삽입.
    - 규칙: `if supervisor_missing and runtime_state == "RUNNING" and has_active_surface`:
      - `if not updated_at` 이면 `DEGRADED` + `supervisor_missing_snapshot_undated`.
      - `elif snapshot_age <= 15.0` 이면 `DEGRADED` + `supervisor_missing_recent_ambiguous`.
      - 이 분기에서는 레인 상태(`state`)를 보존하되 `pid`와 `attachable`만 정규화함.
  - `tests/test_pipeline_gui_backend.py` 수정:
    - `:1012, :1195, :1257` 부근의 `@unittest.skip` 데코레이터 3건 제거.
  - `python3 -m unittest tests/test_pipeline_gui_backend` 실행 결과 `OK (skipped=0)` 확인.

## 결론
G5-unskip-DEGRADED-FAMILY를 통해 GUI 백엔드 테스트의 마지막 공백을 메우고, 모든 상태 전이 시나리오를 정직하게 구현할 것을 추천함.
