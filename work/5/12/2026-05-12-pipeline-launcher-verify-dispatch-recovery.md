# 2026-05-12 Pipeline launcher verify dispatch recovery

## 변경 파일

- `verify_fsm.py`
- `watcher_state.py`
- `watcher_dispatch.py`
- `tests/test_watcher_core.py`
- `work/5/12/2026-05-12-pipeline-launcher-verify-dispatch-recovery.md`
- `verify/5/12/2026-05-12-pipeline-launcher-verify-dispatch-recovery.md`

## 사용 skill

- `security-gate`: tmux/Codex 자동 입력, runtime dispatch, 로컬 로그 경계를 다시 점검했습니다.
- `round-handoff`: 멈춘 verify job의 실제 상태와 최신 `/work`/`/verify` 진실을 분리해 기록했습니다.
- `work-log-closeout`: 변경 파일, 검증, 남은 리스크를 표준 `/work` 형식으로 남겼습니다.

## 변경 이유

- `work/5/12/2026-05-12-pipeline-launcher-stale-pasted-recovery.md` 검증 라운드가 Codex verify dispatch에서 다시 멈췄습니다.
- 첫 번째 원인은 verify FSM requeue 이후 dedupe 해제가 프로세스 재시작 후 유지되지 않아 `reason=dedupe`로 재시도가 막힌 점이었습니다.
- 두 번째 원인은 Codex prompt가 실제로는 입력줄에 남아 있는데 과거 출력의 활동 marker 때문에 `_dispatch_codex()`가 submit 성공으로 오판한 점이었습니다.

## 핵심 변경

- `verify_fsm.py`가 입력 프롬프트의 unsubmitted `[Pasted Content N chars]`를 실패 스냅샷으로 고정하지 않고, 이전에 저장된 pasted prompt 스냅샷도 clearable draft로 보고 재시도할 수 있게 했습니다.
- requeued failed dispatch는 duplicate check 전에 `dedupe.forget()`을 한 번 더 수행해, 기존 프로세스 재시작 이후에도 stale dispatch key가 재시도를 막지 않게 했습니다.
- `watcher_state.DedupeGuard.forget()`이 `dispatch.jsonl`에 `event: forget` tombstone을 남기고, reload 시 이 tombstone을 반영하도록 했습니다.
- `watcher_dispatch._dispatch_codex()`가 Enter 이후에도 unsubmitted pasted prompt가 남아 있으면 성공으로 보지 않게 했습니다.
- 관련 회귀 테스트를 추가해 stale pasted prompt retry, dedupe tombstone persistence, Codex pasted prompt false-success 방지를 고정했습니다.

## 검증

- PASS: `python3 -m unittest -v tests.test_watcher_core.DedupeGuardPersistenceTest tests.test_watcher_core.PanePromptDetectionTest tests.test_watcher_core.CodexDispatchConfirmationTest tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest tests.test_watcher_core.VerifyPendingBackoffTest` (35 tests)
- PASS: `python3 -m py_compile verify_fsm.py watcher_state.py watcher_dispatch.py pipeline_runtime/lane_surface.py tests/test_watcher_core.py`
- PASS: `git diff --check -- verify_fsm.py watcher_state.py watcher_dispatch.py pipeline_runtime/lane_surface.py tests/test_watcher_core.py`

## 남은 리스크

- live Codex pane의 기존 pasted draft는 이번 코드 변경 전에 이미 누적되어 있어서 수동으로 입력줄을 비워야 합니다.
- 현재 run은 기존 job이 두 번째 dispatch stall까지 도달해 `dispatch_stall` degraded 상태가 되었으므로, matching `/verify` 기록으로 truth를 닫은 뒤 다음 라운드가 이어져야 합니다.
- 브라우저/E2E와 장시간 soak는 실행하지 않았습니다. 이번 검증은 pipeline launcher dispatch/FSM 단위 회귀와 live 상태 관측에 한정했습니다.
