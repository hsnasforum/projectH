# 2026-05-21 Codex v0.132 paste submit fallback

## 변경 파일

- `watcher_dispatch.py`
- `pipeline_runtime/lane_surface.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/5/21/2026-05-21-codex-v0132-paste-submit-fallback.md`

## 사용 skill

- `security-gate`: tmux 자동 입력, Codex pane submit, stale prompt 차단, fallback 실행 경계를 점검하기 위해 사용했다.
- `doc-sync`: runtime dispatch 계약이 바뀐 내용을 pipeline README와 runtime 설계/운영 문서에 맞추기 위해 사용했다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유

- Codex CLI v0.132.0에서 watcher가 붙여넣은 `[Pasted Content ...]` prompt가 첫 `Enter` 뒤에도 입력줄에 남아 `pasted_prompt_after_submit` 계열 fail-closed가 반복됐다.
- 긴 v0.132.0 TUI 입력은 prompt 시작 줄이 최근 12줄 밖으로 밀릴 수 있어 기존 `pane_text_has_unsubmitted_pasted_content()`가 visible pasted marker를 놓쳤고, watcher가 실제 미제출 입력을 "소비됨"으로 오판할 수 있었다.
- pre-existing stale paste를 덮어쓰지 않는 기존 안전 경계는 유지하되, watcher가 방금 붙인 fresh prompt에 대해서만 bounded submit 보강과 cleanup-confirmed fallback이 필요했다.

## 핵심 변경

- `pane_text_has_unsubmitted_pasted_content()`가 visible pane 전체에서 마지막 input prompt 이후의 `[Pasted Content ...]` marker를 찾도록 바꿨다.
- `WatcherDispatchQueue.lane_prompt_readiness()`는 idle 판정보다 먼저 unsubmitted pasted content를 검사해 긴 wrapped paste도 `prompt_contains_pasted_content`로 차단한다.
- Codex paste dispatch는 fresh paste가 첫 `Enter` 뒤 남으면 `C-j`를 한 번 더 보내고, 그래도 남으면 cleanup을 먼저 확인한다.
- cleanup으로 입력줄이 비워진 경우에만 one-line literal fallback을 한 번 실행한다. cleanup 실패나 fallback 실패는 기존처럼 fail-closed 한다.
- v0.132.0 wrapped paste, cleanup 실패 시 fallback 금지, cleanup 성공 시 fallback 진입, live submit fallback 성공 경로를 테스트와 문서에 반영했다.

## 검증

- `python3 -m py_compile watcher_dispatch.py pipeline_runtime/lane_surface.py tests/test_watcher_core.py`
  - 통과.
- `python3 -m unittest -v tests.test_watcher_core.PanePromptDetectionTest tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest tests.test_watcher_core.CodexDispatchConfirmationTest tests.test_watcher_core.VerifyPendingBackoffTest`
  - 통과. `Ran 58 tests in 6.592s` / `OK`.
- `git diff --check -- watcher_dispatch.py pipeline_runtime/lane_surface.py tests/test_watcher_core.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 통과.
- `python3 -m pipeline_runtime.cli restart . --no-attach`
  - 실행. 기존 stuck Codex pane을 새 run으로 정리했다.
- live watcher log 확인
  - `codex pasted prompt still visible after Enter; retrying with C-j once`
  - `retrying codex dispatch via literal fallback after pasted prompt cleanup`
  - `codex response activity detected after literal fallback submit`
- live runtime status 확인
  - `runtime_state=RUNNING`, `automation_health=ok`, `automation_next_action=continue`
  - wrapper events에서 `DISPATCH_SEEN` 뒤 `TASK_ACCEPTED`가 기록되어 v0.132.0 dispatch가 수락됨을 확인했다.

## 남은 리스크

- full unittest, Playwright, controller smoke, long soak는 실행하지 않았다. 변경 범위가 Codex dispatch/pane surface detection에 한정되어 관련 unit과 live dispatch acceptance를 우선 확인했다.
- literal fallback은 cleanup 성공 후 1회만 허용된다. pre-existing stale paste, cleanup 실패, fallback submit 실패는 계속 fail-closed 한다.
- live verify round는 `TASK_ACCEPTED` 이후 `VERIFYING` 상태로 진행 중이었다. 이 closeout은 dispatch 수락 회귀 수정까지를 검증 범위로 삼고, verify 결과 자체는 별도 `/verify` 흐름이 맡는다.
- commit, push, PR publication, merge, release는 수행하지 않았다.
