# 2026-04-21 stale advisory operator guard

## 변경 파일
- `watcher_core.py`
- `tests/test_watcher_core.py`
- `work/4/21/2026-04-21-stale-advisory-operator-guard.md`

## 사용 skill
- `security-gate`: runtime control slot 자동 작성 경로가 활성 operator gate를 침범하지 않는지 확인했습니다.
- `finalize-lite`: handoff 지정 범위, 실행한 검증, 문서 동기화 필요 여부, `/work` closeout 준비 상태를 확인했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행한 명령만 기준으로 이 closeout을 남겼습니다.

## 변경 이유
- `_maybe_write_stale_control_advisory_request`가 stale control 상태에서 `.pipeline/gemini_request.md`를 자동 작성할 때, 현재 활성 `.pipeline/operator_request.md`가 `STATUS: needs_operator`인 경우를 먼저 막아야 했습니다.
- 이번 slice는 합법적인 operator stop을 stale advisory 요청이 supersede하지 않도록 하는 좁은 runtime-control 안전 보강입니다.

## 핵심 변경
- `_advisory_enabled()` 확인 직후 활성 control이 `.pipeline/operator_request.md`의 `needs_operator`이면 stale advisory 자동 작성을 중단하도록 조기 반환을 추가했습니다.
- control age가 threshold + grace에 도달해도 활성 `needs_operator`가 있으면 `_maybe_write_stale_control_advisory_request()`가 `False`를 반환하는 회귀 테스트를 추가했습니다.
- 새 테스트는 `_notify_gemini`가 호출되지 않고, `.pipeline/gemini_request.md`가 작성되지 않으며, 기존 `operator_request.md` 본문이 유지되는지 확인합니다.
- `.pipeline/claude_handoff.md`, `.pipeline/gemini_request.md`, `.pipeline/operator_request.md`는 수정하지 않았습니다.
- 문서 동기화는 수행하지 않았습니다. 사용자-facing 계약 변경이 아니라 기존 operator gate 우선순위를 지키는 내부 runtime guard입니다.

## 검증
- `python3 -m py_compile watcher_core.py` -> 통과
- `python3 -m unittest tests.test_watcher_core -v` -> 175 tests OK
- `git diff --check -- watcher_core.py tests/test_watcher_core.py` -> 통과

## 남은 리스크
- live tmux watcher 실행 검증은 수행하지 않았습니다. 이번 round는 `tests.test_watcher_core` 단위 테스트 범위로 제한했습니다.
- `watcher_core.py`와 `tests/test_watcher_core.py`에는 이전 seq 작업에서 남은 uncommitted 변경이 함께 있습니다. 이 closeout은 이번 handoff의 operator guard 추가만 기록합니다.
- commit, push, branch/PR publish, next-slice 선택은 수행하지 않았습니다.
