# 2026-04-20 AXIS-G4 Stall Prevention Arbitration

## 개요
- **상태**: `advice_ready`
- **시퀀스**: 592
- **대상**: AXIS-G4 (Supervisor-side Stall Prevention)
- **권고 슬라이스**: (A) AXIS-G4 second widening — supervisor-side deferral

## 판단 근거
1. **우선순위 (GEMINI.md)**: AXIS-G4는 현재 발생 중인 런타임 Stall(멈춤)을 해결하는 작업으로, `same-family current-risk reduction` (우선순위 1)에 해당합니다.
2. **완결성**: seq 587에서 구현된 `WatcherDispatchQueue`의 감시 로직은 Stall을 "관측 가능"하게 만들었지만, 원천적인 "방지"는 Supervisor(생성자) 측에서 이루어져야 합니다.
3. **포화도 규칙 회피**: 오늘(2026-04-20) 이미 3회의 docs-only 라운드가 진행되어 포화 상태입니다. 후보 (B)와 (C)는 docs-only 성격이 강해 지양해야 하며, 후보 (A)는 실질적인 코드/테스트 개선을 포함하는 건강한 다음 단계입니다.
4. **리스크 통제**: Supervisor 측에서 `lane_working` 전이를 억제함으로써, 불완전한 상태가 파이프라인 전체로 전파되는 것을 차단합니다.

## 권고 세부 사항 (IMPLEMENT_PIN)
- **수정 모듈**: `pipeline_runtime/supervisor.py`
- **수정 위치**: `_build_lane_statuses` 메서드 내 `state = "WORKING"` 전이 로직 (line 1087~1114 부근).
- **로직 상세**:
    - tmux pane에서 busy indicator가 감지(`tail_surface == "WORKING"`)되더라도, 해당 `control_seq`에 대응하는 Wrapper 영수증(`DISPATCH_SEEN` 또는 `TASK_ACCEPTED`)이 확인되지 않으면 `state`를 `"WORKING"`으로 전이하지 않습니다.
    - 대신 `state`를 `"READY"`(또는 `BOOTING`)로 유지하고, `note`에 `"signal_mismatch"`를 남겨 `_write_status`가 `lane_working` 이벤트를 발행하지 않도록 제어합니다.
- **검증 (Test)**:
    - `tests/test_pipeline_runtime_supervisor.py`에 새 테스트 `test_build_lane_statuses_defers_working_on_signal_mismatch`를 추가합니다.
    - Tmux pane은 WORKING으로 보이지만 Wrapper 이벤트는 비어 있는 상황을 Mock으로 주입하고, Supervisor 모델의 `state`가 `WORKING`이 아닌지 검증합니다.
- **제약**: `watcher_dispatch.py`, `watcher_core.py` 또는 Wrapper 코드는 이번 슬라이스에서 수정하지 않습니다.

## 남은 리스크
- `BusyLaneNotificationDeferTest`의 assertion flip(`assertTrue`)에 대한 정당성 검토(후보 B)는 이번 라운드에서 제외되므로, 해당 테스트의 계약 적합성은 사후 감사가 필요합니다.
- `watcher_core` 테스트 카운트 drift(143 -> 149)는 인지된 상태로 유지되며, G5 베이스라인 재핀(후보 C)은 다음 기회로 미룹니다.
