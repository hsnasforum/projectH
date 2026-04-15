## 변경 파일
- watcher_core.py
- tests/test_watcher_core.py

## 사용 skill
- 없음

## 변경 이유
- Claude pane이 `STATUS:` 다음 줄에 `implement_blocked`를 출력하는 형태로 sentinel을 남겼을 때 watcher가 이를 감지하지 못해 automation이 `Claude READY` 상태로 멈출 수 있었습니다.
- 실제 런타임 tail에서 같은 형태가 재현되었고, 현재 handoff는 stale `implement` control에 머무른 채 Codex triage로 넘어가지 못했습니다.

## 핵심 변경
- `watcher_core._extract_claude_implement_blocked_signal(...)`가 wrapped `STATUS:` / wrapped `BLOCK_REASON:` / wrapped `HANDOFF_SHA:` / wrapped `BLOCK_ID:`를 처리하도록 보강했습니다.
- `BLOCK_REASON` 다중 줄은 공백을 유지해 이어붙이도록 해 triage prompt의 이유 문자열이 더 자연스럽게 남도록 했습니다.
- 실제 pane 형태와 가까운 `STATUS:` 줄바꿈 regression test를 `tests/test_watcher_core.py`에 추가했습니다.

## 검증
- `python3 -m py_compile watcher_core.py tests/test_watcher_core.py`
- `python3 -m unittest -v tests.test_watcher_core.ClaudeImplementBlockedTest`

## 남은 리스크
- 이번 수정은 watcher sentinel extractor 보강입니다. 이미 멈춰 있던 기존 run을 완전히 되살리는 보장은 없고, 당시 pane state/turn state 조합에 따라 수동 재시작이나 새 poll 사이클이 필요할 수 있습니다.
- Claude가 sentinel 이후 다시 작업을 재개하면, 해당 pane tail만 기준으로는 “실패 후 회복”과 “원래부터 계속 진행”이 혼재해 보일 수 있습니다.
