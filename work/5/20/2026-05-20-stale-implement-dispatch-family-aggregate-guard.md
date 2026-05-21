# 2026-05-20 stale implement dispatch family aggregate guard

## 변경 파일
- `work/5/20/2026-05-20-stale-implement-dispatch-family-aggregate-guard.md`

## 사용 skill
- `work-log-closeout`: aggregate guard 실행 사실, 실제 변경 파일, 검증, 생략한 검증, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유
- stale implement dispatch incident family에서 immediate signal path, direct dispatch mismatch path, queued pending notification path가 모두 더 높은 `CONTROL_SEQ` advisory control 아래에서 stale handoff를 전달하지 않는지 한 번에 확인해야 했습니다.
- 기존 focused tests가 세 표면을 이미 직접 고정하고 있어, 추가 aggregate test는 동일 assertion 중복만 만들 가능성이 높았습니다.

## 핵심 변경
- runtime source와 test source는 이번 라운드에서 추가 수정하지 않았습니다.
- 기존 focused tests를 aggregate guard로 함께 재실행해 세 표면을 확인했습니다.
- `test_higher_seq_advisory_keeps_stale_handoff_signal_unconsumed`로 active advisory가 stale handoff signal consumption을 막는 경로를 확인했습니다.
- `test_stale_implement_dispatch_drops_when_higher_seq_advisory_is_active`로 direct implement dispatch가 active advisory 아래에서 전송되지 않는 경로를 확인했습니다.
- `test_flush_pending_drops_stale_implement_when_higher_seq_advisory_is_active`로 queued pending implement notification이 active advisory 아래에서 drop되는 경로를 확인했습니다.

## 검증
- `rg -n "test_higher_seq_advisory_keeps_stale_handoff_signal_unconsumed|test_stale_implement_dispatch_drops_when_higher_seq_advisory_is_active|test_flush_pending_drops_stale_implement_when_higher_seq_advisory_is_active" tests/test_watcher_core.py`
  - 결과: PASS. 세 focused test 위치를 확인했습니다.
- `python3 -m py_compile watcher_core.py watcher_dispatch.py tests/test_watcher_core.py`
  - 결과: PASS
- `python3 -m unittest -v tests.test_watcher_core.RollingSignalTransitionTest.test_higher_seq_advisory_keeps_stale_handoff_signal_unconsumed tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_implement_dispatch_drops_when_higher_seq_advisory_is_active tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_flush_pending_drops_stale_implement_when_higher_seq_advisory_is_active tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_flush_pending_logs_structured_control_seq_drift`
  - 결과: PASS, 4개 테스트 통과
- `git diff --check -- work/5/20/2026-05-20-stale-implement-dispatch-family-aggregate-guard.md watcher_core.py watcher_dispatch.py tests/test_watcher_core.py`
  - 결과: PASS, 출력 없음
- `git diff --check --no-index -- /dev/null work/5/20/2026-05-20-stale-implement-dispatch-family-aggregate-guard.md`
  - 결과: PASS. 새 파일 비교라 exit code는 1이지만 whitespace error 출력은 없었습니다.

## 생략한 검증
- `tmux`, lane-local `status --json`, `doctor --json`는 handoff 금지 항목이라 실행하지 않았습니다.
- Playwright, controller smoke, full `make e2e-test`, release smoke, long soak, socket-bound HTTP 테스트는 실행하지 않았습니다.
- commit, push, branch/PR publish, PR creation/reuse/update, merge, release는 실행하지 않았습니다.

## 남은 리스크
- `watcher_core.py`, `watcher_dispatch.py`, `tests/test_watcher_core.py`에는 이전 라운드의 dirty changes가 함께 섞여 있습니다. 이번 라운드는 새 source/test 변경 없이 aggregate guard evidence와 `/work` closeout만 추가했습니다.
- 전체 dirty bundle, browser-visible behavior, live runtime reload, socket-bound runtime surface는 이번 handoff 범위 밖이라 release readiness를 주장하지 않습니다.
