## 변경 파일
- watcher_core.py
- tests/test_watcher_core.py

## 사용 skill
- 없음

## 변경 이유
- `claude_handoff.md`가 갱신되면 watcher가 `slot_verify`가 아직 살아 있는 동안에도 Claude pane에 다음 implement handoff를 다시 보내는 경우가 있었습니다.
- 이 때문에 Claude가 방금 끝낸 슬라이스와 다음 슬라이스를 겹쳐 읽거나, operator가 보기에 규칙이 안 먹는 것처럼 보이는 혼선이 생겼습니다.

## 핵심 변경
- `watcher_core.py`에 Claude handoff dispatch 상태 계산 helper를 추가했습니다.
- `slot_verify` lease가 active인 동안에는 `STATUS: implement` handoff 갱신이 보여도 즉시 Claude notify를 보내지 않고 pending으로 보류하게 했습니다.
- verify lease가 해제된 뒤 handoff 시그니처가 그대로 남아 있으면, pending handoff를 Claude에 한 번만 flush 하도록 했습니다.
- `tests/test_watcher_core.py`에 `handoff update waits until verify lease released` 회귀 테스트를 추가했습니다.

## 검증
- `python3 -m py_compile watcher_core.py tests/test_watcher_core.py`
- `python3 -m unittest -v tests.test_watcher_core`
- `git diff --check -- watcher_core.py tests/test_watcher_core.py`

## 남은 리스크
- 이 수정은 `handoff update`가 verify lease보다 먼저 나가는 경로를 막습니다.
- 다만 pane capture 지연이나 UI poll stale처럼 표시 계층에서 생기는 혼선은 별도 축으로 남아 있습니다.
