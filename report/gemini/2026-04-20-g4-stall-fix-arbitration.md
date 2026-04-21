# 2026-04-20 AXIS-G4 Stall Fix Arbitration

## 개요
- **상태**: `advice_ready`
- **시퀀스**: 586
- **대상**: AXIS-G4 (Supervisor-Wrapper Signal Mismatch Stall)
- **권고 슬라이스**: (A) `watcher_dispatch.py` 내 `WatcherDispatchQueue`를 통한 mismatch 감시 및 Fix

## 판단 근거
1. **우선순위 (GEMINI.md)**: AXIS-G4는 현재 관측된 Stall(멈춤) 현상을 다루며, 이는 `same-family current-risk reduction` (우선순위 1)에 해당합니다.
2. **경계 고정**: 이전 라운드(seq 584)에서 수집된 trace 증거(`runs/20260420T142213Z-p817639`)는 Supervisor의 `lane_working` 신호와 Wrapper의 `HEARTBEAT` 전용 스트림 사이의 불일치를 명확히 보여주었습니다. 이 상호작용의 경계인 `WatcherDispatchQueue`에서 이를 제어하는 것이 가장 직접적인 해결책입니다.
3. **타 후보 비교**:
    - (B) `test_blocked_triage_defers_until_codex_prompt_is_ready` 실패는 dirty worktree의 기존 회귀이며 별도 axis입니다.
    - (C) AXIS-G6 (Web App)는 신규 axis로 우선순위가 낮습니다.
    - (D) Verify-lane 전용 작업은 구현 진척을 만들지 않습니다.

## 권고 세부 사항 (IMPLEMENT_PIN)
- **수정 모듈**: `watcher_dispatch.py` (WatcherDispatchQueue 클래스)
- **수정 로직**:
    - `WatcherDispatchQueue`가 Supervisor의 `lane_working` 상태(또는 `WORKING` 전이)를 인지하되, Wrapper의 `DISPATCH_SEEN` 또는 `TASK_ACCEPTED` 영수증이 일정 시간 내에 관측되지 않는 경우 이를 `signal_mismatch`로 판정합니다.
    - mismatch 판정 시 `lane_input_deferred_dropped` 이벤트를 `reason_code: signal_mismatch`와 함께 방출하여 Stall이 침묵 속에 지속되지 않도록 합니다.
- **검증 (Test)**:
    - `tests/test_watcher_core.py:2297`의 `test_dispatch_signal_mismatch_supervisor_working_without_wrapper_receipt`에 적용된 `@unittest.skip`을 제거합니다.
    - Mock을 사용하여 Supervisor `WORKING` + Wrapper `HEARTBEAT`-only 상황을 주입하고, `WatcherDispatchQueue`가 이를 mismatch로 정확히 분류하여 이벤트를 기록하는지 검증합니다.
- **제약**: `watcher_dispatch.py` 외의 프로덕션 모듈 수정이나 대규모 리팩토링은 이번 슬라이스 범위 밖입니다.

## 남은 리스크
- dirty worktree에 남아 있는 `BusyLaneNotificationDeferTest` 실패는 이번 슬라이스에서 다루지 않으므로, 전체 테스트 통과(`146 green`)는 다음 cleanup 슬라이스까지 미뤄집니다.
