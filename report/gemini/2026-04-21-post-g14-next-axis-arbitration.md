# 2026-04-21 Post-G14 Next Axis Arbitration (CONTROL_SEQ 615)

## 개요
- **Arbitration 대상**: CONTROL_SEQ 614 이후 차기 implement 축 결정
- **결정**: AXIS-G15 (Technical Integrity: Watcher Test Baseline 151) 추천
- **상태**: G14 (vocab normalization) 및 verify_fsm fallback 완료로 `feat/watcher-turn-state` 브랜치 목표 달성.

## 판단 근거
1. **Technical Integrity (Risk Reduction)**: 최근 라운드(seq 593, 605, 613)에서 반복적으로 관찰된 "미기록 테스트 추가(undocumented scope addition)" 패턴이 `tests/test_watcher_core.py`에서도 확인되었습니다 (baseline 149 -> 실측 151). G13이 supervisor 테스트를 106으로 동기화한 것과 마찬가지로, watcher 테스트도 151로 truth-sync하여 브랜치를 깨끗하게 닫는 것이 우선순위가 높습니다.
2. **Axis 전환 전 완결성**: `pipeline_runtime` 인프라 작업의 마지막 조각인 G14가 닫혔으므로, 남은 미세한 drift를 정리하여 "seq 593/605 패턴 지속" 리스크를 해소하는 것이 다음 milestone(Milestone 5)으로 넘어가기 전의 논리적 순서입니다.
3. **타 Axis 배제**:
   - **AXIS-G6 (PermissionError)**: 현재 verify-lane에서 환경(sandbox) vs 코드(bind address) 원인 분석이 선행되어야 합니다. 분석 결과가 나오기 전까지 implement-lane이 개입하기에는 모호성이 큽니다.
   - **AXIS-DISPATCHER-TRACE-BACKFILL**: 여전히 verify-lane의 `events.jsonl` 정합성 체크 영역입니다.
   - **Milestone 4/5**: 인프라 브랜치의 integrity sync(G15)가 10분 내외의 작은 슬라이스로 가능하므로, 이를 먼저 닫고 깨끗한 상태에서 milestone 전환을 권고합니다.

## 추천 Slice 상세
- **Title**: `AXIS-G15 (Technical Integrity: Watcher Test Baseline 151)`
- **목적**: `tests/test_watcher_core.py`의 테스트 카운트를 151로 동기화하고, 미기록된 테스트들에 기원(origin) 주석을 추가하여 pipeline integrity를 확보합니다.
- **범위**:
  - `tests/test_watcher_core.py`:
    - `test_late_old_task_done_does_not_close_new_dispatch` (undocumented)에 기원 주석 추가.
    - `test_outputs_complete_infers_task_done_after_done_deadline_when_wrapper_misses_done` (fallback)에 기원 주석 추가.
- **검증**: `python3 -m unittest tests.test_watcher_core` (Ran 151 tests / OK 확인)

## 차기 가이드
- **Verify-lane**: AXIS-G6 `PermissionError`에 대해 `strace` 등을 이용한 상세 원인 조사를 우선 수행할 것을 권고합니다.
- **Codex**: AXIS-G15 이후에는 Milestone 5 (Grounded Brief Contract) 영역으로의 축 전환을 준비합니다.
