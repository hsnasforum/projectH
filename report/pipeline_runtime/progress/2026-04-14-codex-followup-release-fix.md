# Pipeline Runtime codex followup release fix

## 변경 파일
- watcher_core.py
- tests/test_watcher_core.py
- report/pipeline_runtime/verification/2026-04-14-codex-followup-release-synthetic-pass.md

## 사용 skill
- 없음

## 변경 이유
- 실행 중이던 24시간 synthetic-soak의 상태 파일과 run-scoped 로그를 확인한 결과, `CONTROL_SEQ=7` handoff가 써진 뒤에도 `turn_state.json`이 `CODEX_FOLLOWUP`에 머물렀고 `task-hints/codex.json`이 계속 `active=true`로 남아 다음 Claude implement round가 시작되지 않았습니다.
- watcher 로그 기준으로는 `gemini_request -> gemini_advice -> codex followup -> claude_handoff(seq7)`까지는 정상 진행됐지만, verify receipt가 기록된 뒤 `verify_lease_released`를 Claude로 flush하는 경로가 `CODEX_FOLLOWUP` 상태를 허용하지 않아 그 자리에서 정지했습니다.

## 핵심 변경
- `watcher_core._flush_pending_claude_handoff()`가 `WatcherTurnState.CODEX_FOLLOWUP`에서도 verify lease 해제 후 Claude handoff flush를 수행하도록 수정했습니다.
- 회귀 테스트에 `CODEX_FOLLOWUP` 상태에서 lease release 후 `CLAUDE_ACTIVE`로 정상 전이되는 케이스를 추가했습니다.
- 짧은 synthetic soak를 다시 돌려 receipt 5에서 멈추던 지점을 넘어 receipt 10까지 이어지는지 확인했습니다.

## 검증
- `python3 -m py_compile watcher_core.py tests/test_watcher_core.py`
- `python3 -m unittest -v tests.test_watcher_core.ClaudeHandoffDispatchTest tests.test_watcher_core.PanePromptDetectionTest tests.test_watcher_core.ClaudeImplementBlockedTest`
- `python3 scripts/pipeline_runtime_gate.py --project-root /home/xpdlqj/code/projectH --mode experimental synthetic-soak --duration-sec 260 --sample-interval-sec 2 --min-receipts 6 --report /home/xpdlqj/code/projectH/report/pipeline_runtime/verification/2026-04-14-codex-followup-release-synthetic-pass.md`
- synthetic soak 결과:
  - `receipt_count=10`
  - `broken_seen=False`
  - `degraded_counts={}`
  - `duplicate_dispatch_count=0`
  - `control_mismatch_max_streak=1`

## 남은 리스크
- 지금 사용자가 돌리고 있는 24시간 synthetic-soak는 이 패치 전 프로세스이므로 hot-reload되지 않습니다. 그 런은 최종 채택 근거로 쓸 수 없고, 패치 반영 상태에서 다시 시작해야 합니다.
- 이번 수정으로 `CODEX_FOLLOWUP` 정지는 막았지만, wrapper가 같은 task에 대해 `TASK_ACCEPTED/TASK_DONE`를 반복 기록하는 noisy event 패턴은 별도 정리 여지가 남아 있습니다.
