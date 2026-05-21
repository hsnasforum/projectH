# 2026-05-20 stale implement pending dispatch after advisory control guard

## 변경 파일
- `tests/test_watcher_core.py`
- `work/5/20/2026-05-20-stale-implement-pending-dispatch-after-advisory-control-guard.md`

## 사용 skill
- `work-log-closeout`: handoff 실행 결과, 실제 변경 파일, 검증, 생략한 검증, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유
- 이전 라운드에서 stale implement immediate dispatch guard는 검증되었지만, 이미 deferred queue에 들어간 stale implement notification이 더 높은 `CONTROL_SEQ` advisory control 아래에서 재전송되지 않는지도 회귀 테스트로 고정할 필요가 있었습니다.

## 핵심 변경
- `WatcherDispatchQueue.flush_pending()`에 대해 stale pending implement notification 회귀 테스트를 추가했습니다.
- 테스트는 `implement_handoff.md#2019` pending notification이 남아 있고 active control이 `advisory_request.md#2022`인 상황을 구성합니다.
- 기대 동작으로 `tmux_send_keys` 미호출, pending 제거, `lane_input_deferred_dropped` 구조화 로그, `reason_code=control_file_drift`, expected/active seq 및 path 기록을 확인합니다.
- 기존 `flush_pending()` mismatch 처리로 이미 통과하는 경로라 runtime source 코드는 추가 수정하지 않았습니다.

## 검증
- `python3 -m py_compile watcher_dispatch.py tests/test_watcher_core.py`
  - 결과: PASS
- `python3 -m unittest -v tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_flush_pending_drops_stale_implement_when_higher_seq_advisory_is_active tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_flush_pending_logs_structured_control_seq_drift tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_pending_control_path_accepts_legacy_alias_for_same_slot tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_implement_dispatch_drops_when_higher_seq_advisory_is_active`
  - 결과: PASS, 4개 테스트 통과
- `git diff --check -- tests/test_watcher_core.py work/5/20/2026-05-20-stale-implement-pending-dispatch-after-advisory-control-guard.md`
  - 결과: PASS, 출력 없음
- `git diff --check --no-index -- /dev/null work/5/20/2026-05-20-stale-implement-pending-dispatch-after-advisory-control-guard.md`
  - 결과: PASS. 새 파일 비교라 exit code는 1이지만 whitespace error 출력은 없었습니다.

## 생략한 검증
- `tmux`, lane-local `status --json`, `doctor --json`는 handoff 금지 항목이라 실행하지 않았습니다.
- Playwright, controller smoke, full `make e2e-test`, release smoke, long soak, socket-bound HTTP 테스트는 실행하지 않았습니다.
- commit, push, branch/PR publish, PR creation/reuse/update, merge, release는 실행하지 않았습니다.

## 남은 리스크
- `watcher_core.py`, `watcher_dispatch.py`, `tests/test_watcher_core.py`에는 이전 라운드의 dirty changes가 함께 섞여 있습니다. 이번 라운드의 새 변경은 pending dispatch regression test 추가에 한정됩니다.
- 전체 dirty bundle, browser-visible behavior, live runtime reload, socket-bound runtime surface는 이번 handoff 범위 밖이라 release readiness를 주장하지 않습니다.
