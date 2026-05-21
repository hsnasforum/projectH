# 2026-05-20 stale implement dispatch after advisory control guard

## 변경 파일
- `watcher_dispatch.py`
- `watcher_core.py`
- `tests/test_watcher_core.py`
- `work/5/20/2026-05-20-stale-implement-dispatch-after-advisory-control-guard.md`

## 사용 skill
- `work-log-closeout`

## 변경 이유
- 더 높은 `CONTROL_SEQ`의 `.pipeline/advisory_request.md`가 active control인데도 낮은 `CONTROL_SEQ`의 `.pipeline/implement_handoff.md`가 반복 전달되는 stale implement redispatch 위험을 막기 위해 수정했습니다.

## 핵심 변경
- `WatcherDispatchQueue.dispatch()`가 `require_active_control`이 설정된 즉시 dispatch에서도 현재 active control과 기대 slot/status/seq가 맞지 않으면 전송 전에 `lane_input_deferred_dropped`로 구조화해 drop하도록 했습니다.
- `watcher_core._check_pipeline_signal_updates()`가 active control이 다른 slot일 때 비활성 implement handoff 파일의 sig를 fallback으로 소비하지 않게 했습니다.
- 높은 seq advisory control이 낮은 seq implement handoff를 이기는 상황에서 stale handoff sig가 소비되지 않고, stale implement 직접 dispatch가 전송되지 않는 회귀 테스트를 추가했습니다.

## 검증
- `python3 -m py_compile watcher_core.py watcher_dispatch.py tests/test_watcher_core.py`
- `python3 -m unittest -v tests.test_watcher_core.RollingSignalTransitionTest.test_higher_seq_advisory_keeps_stale_handoff_signal_unconsumed tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_implement_dispatch_drops_when_higher_seq_advisory_is_active`
- `python3 -m py_compile watcher_core.py watcher_dispatch.py watcher_prompt_assembly.py pipeline_runtime/turn_arbitration.py pipeline_runtime/control_writers.py tests/test_watcher_core.py`
- `python3 -m unittest -v tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_new_control_dispatch_replaces_stale_codex_pasted_content tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_flush_pending_logs_structured_control_seq_drift tests.test_watcher_core.BusyLaneNotificationDeferTest.test_implement_handoff_notify_defers_until_prompt_is_ready`
- `git diff --check -- watcher_core.py watcher_dispatch.py tests/test_watcher_core.py work/5/20/2026-05-20-stale-implement-dispatch-after-advisory-control-guard.md`
- `git diff --check --no-index -- /dev/null work/5/20/2026-05-20-stale-implement-dispatch-after-advisory-control-guard.md` (출력 없음, `/dev/null` 비교라 exit code 1)

## 생략한 검증
- handoff 지시 범위에 따라 `tmux`, lane-local `status --json`, `doctor --json`, Playwright, controller smoke, full smoke, socket-bound HTTP 테스트는 실행하지 않았습니다.
- 전체 unittest는 기존 dirty tree 범위가 넓어 이번 stale dispatch guard의 직접 경로만 좁게 확인했습니다.

## 남은 리스크
- `watcher_core.py`, `watcher_dispatch.py`, `tests/test_watcher_core.py`에는 이번 라운드 이전의 기존 변경도 섞여 있어, 최종 verify 단계에서는 전체 dirty bundle 관점에서 한 번 더 범위를 확인해야 합니다.
- 이번 변경은 active control mismatch 전송 방지와 stale handoff sig 소비 방지에 한정되어 있으며, branch/PR publish 또는 runtime live socket 검증은 수행하지 않았습니다.
