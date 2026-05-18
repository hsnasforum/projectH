STATUS: verified

# 2026-05-12 Pipeline launcher verify dispatch recovery 검증

## 대상

- `work/5/12/2026-05-12-pipeline-launcher-stale-pasted-recovery.md`
- `work/5/12/2026-05-12-pipeline-launcher-verify-dispatch-recovery.md`

## 변경 파일

- 없음

## 결론

- 부분 통과입니다. 단위 회귀와 compile/diff 검증은 통과했습니다.
- 다만 live run `20260512T043547Z-p50978`의 기존 verify job `20260512-2026-05-12-pipeline-launcher-sta-15290501`은 코드 보완 전에 이미 두 번째 `task_accept_missing`에 도달해 `dispatch_stall` degraded로 고정되었습니다.
- 따라서 현재 shipped truth는 “코드상 재발 방지 회귀는 추가됨, 기존 live degraded job은 matching verify 기록과 입력줄 정리 후 다음 라운드에서 회복 확인 필요”입니다.

## 확인한 사실

- `verify_fsm.py`는 unsubmitted pasted prompt를 실패 스냅샷으로 저장하지 않도록 보완되었습니다.
- `watcher_state.DedupeGuard`는 `forget` tombstone을 영속 로그에 남겨 watcher restart 뒤 stale duplicate key가 되살아나지 않도록 보완되었습니다.
- `watcher_dispatch._dispatch_codex()`는 Enter 이후 pasted prompt가 그대로 남으면 dispatch 성공으로 보지 않도록 보완되었습니다.
- supervisor는 `verify_fsm.py` 변경을 감지해 watcher를 재시작했으며, 이후 dedupe 재시도는 진행됐지만 기존 job은 두 번째 stall로 degraded 처리되었습니다.

## 실행한 검증

- PASS: `python3 -m unittest -v tests.test_watcher_core.DedupeGuardPersistenceTest tests.test_watcher_core.PanePromptDetectionTest tests.test_watcher_core.CodexDispatchConfirmationTest tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest tests.test_watcher_core.VerifyPendingBackoffTest` (35 tests)
- PASS: `python3 -m py_compile verify_fsm.py watcher_state.py watcher_dispatch.py pipeline_runtime/lane_surface.py tests/test_watcher_core.py`
- PASS: `git diff --check -- verify_fsm.py watcher_state.py watcher_dispatch.py pipeline_runtime/lane_surface.py tests/test_watcher_core.py`

## 실행하지 않은 검증

- broad unittest 전체
- browser/E2E
- 장시간 live soak

## 남은 리스크

- live Codex pane에 남은 기존 pasted draft는 코드 변경만으로 사라지지 않습니다.
- 다음 runtime 라운드는 입력줄을 비운 상태에서 새 dispatch가 `TASK_ACCEPTED` 또는 실패 시 `False` 반환/backoff로 관측되는지 확인해야 합니다.
