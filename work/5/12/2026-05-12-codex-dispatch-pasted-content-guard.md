# 2026-05-12 Codex dispatch pasted-content 중복 입력 방지

## 변경 파일

- `pipeline_runtime/lane_surface.py`
- `watcher_dispatch.py`
- `tests/test_watcher_core.py`
- `work/5/12/2026-05-12-codex-dispatch-pasted-content-guard.md`

## 사용 skill

- `security-gate`: tmux/Codex pane 입력 전송과 runtime control follow-up dispatch 경계를 변경하므로, 자동 입력 반복과 local-first runtime 안전성을 점검했습니다.
- `work-log-closeout`: 변경 파일, 검증, 남은 리스크를 표준 `/work` 형식으로 기록했습니다.

## 변경 이유

- Codex pane에서 동일한 follow-up prompt가 `[Pasted Content 1024 chars]`, `#2`, `#3` 형태로 반복 누적되는 문제가 관찰됐습니다.
- 원인은 Codex dispatch가 prompt 소비를 확인하지 못할 때 Enter를 여러 번 재시도하고, dispatch queue가 현재 입력줄에 남은 pasted-content placeholder를 ready prompt로 볼 수 있는 경계가 있었기 때문입니다.

## 핵심 변경

- `pipeline_runtime.lane_surface.pane_text_has_unsubmitted_pasted_content()`를 추가해 현재 입력 prompt 이후에 `[Pasted Content N chars]`가 남아 있는 상태를 감지합니다.
- `WatcherDispatchQueue.lane_prompt_readiness()`가 unsubmitted pasted content를 `prompt_contains_pasted_content` defer reason으로 분류해 같은 pending follow-up을 다시 paste하지 않도록 했습니다.
- Codex dispatch는 paste 후 Enter를 한 번만 누르도록 줄였습니다. prompt가 그대로 보이면 실패로 기록하되, 같은 입력에 Enter를 반복해 pasted block을 누적하지 않습니다.
- `advisory_advice_followup` pending flush가 pasted-content 입력줄을 다시 paste하지 않는 회귀 테스트를 추가했습니다.
- 기존 verify dispatch backoff 계열 테스트와 signal mismatch/pending drop 테스트가 유지되는지 확인했습니다.

## 검증

- PASS: `python3 -m unittest -v tests.test_watcher_core.PanePromptDetectionTest tests.test_watcher_core.CodexDispatchConfirmationTest tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest tests.test_watcher_core.VerifyPendingBackoffTest`
- PASS: `python3 -m py_compile watcher_dispatch.py pipeline_runtime/lane_surface.py tests/test_watcher_core.py`
- PASS: `git diff --check -- watcher_dispatch.py pipeline_runtime/lane_surface.py tests/test_watcher_core.py`

## 남은 리스크

- live tmux 런처 smoke는 실행하지 않았습니다. 이번 검증은 dispatch helper와 watcher queue의 단위 회귀 테스트에 한정했습니다.
- 이미 떠 있는 watcher/launcher 프로세스는 수정된 Python 코드를 자동으로 다시 읽지 않습니다. 현재 세션에 적용하려면 런처/컨트롤러 재시작이 필요합니다.
- 현재 Codex pane에 이미 누적된 pasted-content draft가 남아 있으면 새 코드가 지우지는 않습니다. 입력줄을 비운 뒤 새 런처로 재시작해야 같은 prompt 누적을 끊을 수 있습니다.
