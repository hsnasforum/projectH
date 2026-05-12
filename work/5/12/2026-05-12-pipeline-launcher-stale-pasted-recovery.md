# 2026-05-12 Pipeline launcher stale pasted recovery

## 변경 파일

- `watcher_dispatch.py`
- `tests/test_watcher_core.py`
- `work/5/12/2026-05-12-pipeline-launcher-stale-pasted-recovery.md`

## 사용 skill

- `security-gate`: tmux/Codex pane 입력 전송과 runtime dispatch 복구 경계를 변경하므로, 자동 입력 오염과 local-first runtime audit 경계를 점검했습니다.
- `work-log-closeout`: 변경 파일, 검증, 남은 리스크를 표준 `/work` 형식으로 기록했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md` CONTROL_SEQ 1619의 stale Codex pasted prompt 복구 지시를 실행했습니다.
- 이전 guard는 pending flush가 `[Pasted Content N chars]` 입력줄에 같은 follow-up을 반복 paste하지 않도록 막았지만, 새 active control이 들어왔을 때 기존 stale draft를 교체하는 복구 경로가 필요했습니다.
- 이번 변경은 branch/commit/push/PR publish나 M124/M125 product 선택 없이 pipeline launcher/runtime dispatch 복구에만 한정했습니다.

## 핵심 변경

- `WatcherDispatchQueue.dispatch()`가 fresh dispatch에서 `prompt_contains_pasted_content`를 만나면 stale automation draft replacement로 기록한 뒤 기존 Codex single-submit send path를 한 번 사용하도록 했습니다.
- pending flush(`from_pending=True`)는 기존처럼 `prompt_contains_pasted_content`에서 defer되어 같은 pending follow-up을 다시 paste하지 않습니다.
- `lane_input_stale_pasted_replaced` runtime/raw event를 추가해 deliberate stale-draft recovery와 일반 dispatch를 구분할 수 있게 했습니다.
- `test_new_control_dispatch_replaces_stale_codex_pasted_content`를 추가해 새 control dispatch가 stale pasted content를 교체하고 pending을 남기지 않는 경로를 고정했습니다.
- 이전 slice의 `pipeline_runtime.lane_surface.pane_text_has_unsubmitted_pasted_content()` 감지 helper는 재사용했으며, 이번 handoff에서는 `pipeline_runtime/lane_surface.py`를 새로 수정하지 않았습니다.

## 검증

- PASS: `python3 -m unittest -v tests.test_watcher_core.PanePromptDetectionTest tests.test_watcher_core.CodexDispatchConfirmationTest tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest tests.test_watcher_core.VerifyPendingBackoffTest` (31 tests)
- PASS: `python3 -m py_compile watcher_dispatch.py tests/test_watcher_core.py`
- PASS: `git diff --check -- watcher_dispatch.py tests/test_watcher_core.py .pipeline/implement_handoff.md`

## 남은 리스크

- live launcher/tmux smoke는 실행하지 않았습니다. 이번 검증은 dispatch queue와 Codex send helper의 단위 회귀에 한정했습니다.
- 이미 떠 있는 watcher/launcher 프로세스가 수정된 Python 코드를 자동으로 다시 읽었는지는 확인하지 않았습니다.
- 실제 Codex pane에 남은 stale pasted draft를 새 control dispatch가 교체하는지는 live runtime에서 추가 관측이 필요합니다.
- PR #119-#126 merge 기록은 별도 최신 `/work`로 존재하지만, 이번 handoff 범위가 아니므로 건드리지 않았습니다.
