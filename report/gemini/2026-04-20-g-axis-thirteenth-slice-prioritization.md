# 2026-04-20 G-axis thirteenth slice prioritization

## 개요
- seq 474(G5-unskip-STOPPING)를 통해 첫 번째 상태 전이 규칙(`STOPPING` -> `STOPPED`)이 구현되고 1개의 테스트가 unskip됨.
- 현재 `TestRuntimeStatusRead` 클래스에 8개의 테스트가 스킵 상태로 남아 있음.
- 상태 전이 로직의 정교화 과정을 지속하기 위해, 시스템이 이미 `BROKEN` 상태로 기록되어 있으나 프로세스 감시자(supervisor)가 부재할 때의 어휘 정규화(Vocabulary Normalization)를 수행하는 G5-unskip-DEGRADED_REASON 슬라이스를 다음으로 선정함.

## 판단
1. **current-risk reduction (우선순위 1):**
   - 현재 시스템은 `BROKEN` 상태일 때의 세부 원인(`degraded_reason`)을 파일에 기록된 그대로 보고함. 만약 감시자 프로세스가 죽은 상태에서 기록된 이유가 구식(stale)이라면, 사용자에게 잘못된 원인을 제공하게 됨.
   - G5-unskip-DEGRADED_REASON을 통해 감시자 부재 시 원인을 `"supervisor_missing"`으로 강제 정규화함으로써 진단 정보의 정확성을 높임.

2. **implementation pattern reuse (우선순위 2):**
   - seq 474에서 확립된 `normalize_runtime_status` 확장 패턴(project 인자 수용 및 조기 반환)을 그대로 재사용하여 구현 비용이 낮고 안정적임.
   - 이는 향후 `RUNNING` -> `BROKEN` 전환과 같은 더 복잡한 규칙으로 나아가기 위한 중간 단계로서 가치가 있음.

3. **기타 후보 검토:**
   - **G5-unskip-AGED_AMBIGUOUS:** 시간 임계값 처리가 포함되어 로직이 상대적으로 복잡함.
   - **G3, G6-sub2/3, G7..G11:** 테스트 unskipping 사이클을 완결 짓는 흐름을 유지하는 것이 현재 "Maintenance" 축의 일관성 측면에서 유리함.

## 권고 (RECOMMEND)
- **G5-unskip-DEGRADED_REASON: degraded_reason vocabulary normalization**
- 구체적 범위:
  - `pipeline_gui/backend.py` 수정:
    - `normalize_runtime_status` 내부에 `BROKEN` 상태 정규화 규칙 추가.
    - 규칙: `if supervisor_missing and runtime_state == "BROKEN"` 인 경우, `degraded_reason`과 모든 lane의 `note`를 `"supervisor_missing"`으로 교체하고, 제어 정보(`control`) 및 활성 라운드(`active_round`)를 초기화한 후 반환.
  - `tests/test_pipeline_gui_backend.py` 수정:
    - `test_read_runtime_status_normalizes_broken_payload_when_supervisor_is_missing` (약 `:792`) 메서드 상단의 `@unittest.skip` 제거.
  - `python3 -m unittest tests/test_pipeline_gui_backend` 실행 결과 `OK (skipped=7)` 확인.

## 결론
G5-unskip-DEGRADED_REASON을 통해 진단 정보의 어휘 정합성을 맞추고, GUI 백엔드 테스트의 unskipping 사이클을 지속할 것을 추천함.
