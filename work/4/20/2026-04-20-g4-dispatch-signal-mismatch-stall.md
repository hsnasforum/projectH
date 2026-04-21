# 2026-04-20 g4 dispatch signal mismatch stall

## 변경 파일
- `work/4/20/2026-04-20-g4-dispatch-signal-mismatch-stall.md`
- `tests/test_watcher_core.py`

## 사용 skill
- `onboard-lite`: handoff 범위, evidence run, `WatcherDispatchQueue` test anchor를 좁게 확인했습니다.
- `finalize-lite`: trace-only 라운드의 실제 검증 범위와 `/work` closeout 정합성만 확인했습니다.

## 변경 이유
- Gemini seq 583은 seq 581 G5 shipped 이후 AXIS-G4 stall-trace를 Supervisor↔Wrapper signal mismatch로 pin했습니다.
- 이번 라운드는 runtime stall fix가 아니라, `.pipeline/runs/20260420T142213Z-p817639/`의 증거를 named stall-trace로 고정하고 `WatcherDispatchQueue` 경계에 focused-replay hook을 남기는 trace + skeleton 범위입니다.

## 핵심 변경
- 새 `/work` closeout `work/4/20/2026-04-20-g4-dispatch-signal-mismatch-stall.md`를 만들고, run `20260420T142213Z-p817639`의 seq 233-423를 AXIS-G4 fingerprint로 고정했습니다. mismatch pair는 supervisor source의 `lane_working`(`seq 236`, `seq 245`)과, 같은 Claude cycle 동안 wrapper source에서 `DISPATCH_SEEN` / `TASK_ACCEPTED`가 전혀 기록되지 않고 `wrapper-events/claude.jsonl`에 `HEARTBEAT`만 이어진 상태입니다.
- 첫 WORKING 표시는 `seq 236`(`2026-04-20T14:27:43.555105Z`)이고, 그 뒤 `seq 423`의 supervisor `lane_ready`까지 `dispatch_selection`이 반복되지만 matching wrapper receipt / task_start 계열 확인점은 생기지 않습니다. `receipts/` 디렉터리는 존재하지만 빈 상태이며, 같은 시간 창의 `wrapper-events/claude.jsonl`에는 `HEARTBEAT` 50건만 있고 `DISPATCH_SEEN` / `TASK_ACCEPTED`는 0건입니다.
- 이 trace는 원인을 supervisor state write나 wrapper event emit 한쪽으로 단정하지 않고, 둘 사이 corroboration을 붙이는 `WatcherDispatchQueue` interaction boundary를 이번 핀의 소유 경계로 남깁니다.
- `tests/test_watcher_core.py`에는 `WatcherDispatchQueueControlMismatchTest` 클래스 끝에 `test_dispatch_signal_mismatch_supervisor_working_without_wrapper_receipt`를 `@unittest.skip("AXIS-G4 trace-only: fix slice not yet pinned")`로 1개만 추가했습니다. future focused-replay는 supervisor-side `lane_working`/WORKING 신호와 empty `receipts/`, wrapper-side `HEARTBEAT` only stream(즉 `DISPATCH_SEEN` / `TASK_ACCEPTED` 부재)을 주입하고, queue/dispatcher가 wrapper receipt 없는 dispatch cycle을 조용히 수락하지 않고 mismatch로 계속 관찰 가능하게 두는지를 고정할 자리입니다.
- 정확히 새 `/work` 파일 1개를 만들고 `tests/test_watcher_core.py`에 새 테스트 메서드 1개만 append했습니다. production code, 다른 test, docs 파일, `.pipeline/*` control slot은 건드리지 않았습니다.

## 검증
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 146 tests in 7.492s`, `FAILED (failures=1, skipped=1)`
  - 실패 위치: `tests.test_watcher_core.BusyLaneNotificationDeferTest.test_blocked_triage_defers_until_codex_prompt_is_ready` (`tests/test_watcher_core.py:4654`)
  - 관찰: handoff 기대치인 144 green과 달리 현재 worktree에서는 146건이 실행되었습니다. 이번 라운드에서 append한 새 메서드는 `WatcherDispatchQueueControlMismatchTest`의 skipped skeleton 1건이며, 실패 위치는 별도 구간입니다.
- `python3 -m py_compile tests/test_watcher_core.py`
  - 결과: 성공, 출력 없음
- `git diff --check -- work/4/20/2026-04-20-g4-dispatch-signal-mismatch-stall.md tests/test_watcher_core.py`
  - 결과: 출력 없음

## 남은 리스크
- 이번 라운드는 trace + skeleton만 남겼고 stall fix는 넣지 않았습니다. AXIS-G4 stall-trace는 captured 되었지만 NOT fixed 상태이며, 다음 G4 implement slice는 another trace가 아니라 actual fix여야 합니다.
- handoff의 required verification은 clean green으로 끝나지 않았습니다. 현재 `tests.test_watcher_core` rerun은 146 tests / 1 failure / 1 skipped였고, 실패는 `BusyLaneNotificationDeferTest.test_blocked_triage_defers_until_codex_prompt_is_ready`에 남아 있습니다.
- G5 non-thin-client baseline 5개(`tests.test_pipeline_runtime_supervisor` 101, `tests.test_pipeline_runtime_control_writers` 7, `tests.test_operator_request_schema` 6, `tests.test_pipeline_runtime_schema` 36, `tests.test_watcher_core` 143)는 의도적으로 계속 silent 상태이며, 이번 라운드는 그 count를 다시 pin하지 않습니다.
- AXIS-DISPATCHER-TRACE-BACKFILL queue doc(seq 576)의 trigger met 상태는 그대로이고, 실제 verify-lane 실행은 여전히 pending이며 이번 slice 범위가 아닙니다.
- `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 계속 열려 있고 out of scope입니다.
- seq 527 / 530 / 533 / 536 / 539 / 543 / 546 / 549 / 552 / 555 / 561 / 564 / 567 / 570 / 576 / 581 계약은 byte-for-byte 그대로이며, `.pipeline/operator_request.md` seq 521 canonical literals도 SUPERSEDES chain 558 -> 573 -> 579를 통해 보존된 상태로 남겨 두었습니다.
- 오늘(2026-04-20) same-family docs-only round count는 2로 유지됩니다. 이번 라운드는 code/test이며 docs-only round가 아니므로 3+ saturation rule을 건드리지 않습니다.
- dirty worktree는 두 named 파일 바깥 범위를 그대로 두었고 touch하지 않았습니다.
