# 2026-04-21 AXIS-G15 watcher test origin annotations

## 변경 파일
- `tests/test_watcher_core.py`
- `work/4/21/2026-04-21-axis-g15-watcher-test-origin-annotations.md`

## 사용 skill
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 표준 Korean closeout 형식으로 정리했습니다.

## 변경 이유
- `tests/test_watcher_core.py`에 origin 주석이 없는 watcher test baseline 추가분 2개가 남아 있어, 이후 검증/인수자가 테스트 baseline 증가 원인을 추적하기 어려운 상태였습니다.
- 이번 slice는 순수 truth-sync로, 테스트 동작이나 FSM/runtime 로직을 바꾸지 않고 두 테스트의 발생 라운드만 주석으로 명시했습니다.

## 핵심 변경
- `test_late_old_task_done_does_not_close_new_dispatch` 바로 위에 AXIS-G14 실행 전 dirty worktree에서 발견된 미기록 추가분이라는 origin 주석을 추가했습니다.
- `test_outputs_complete_infers_task_done_after_done_deadline_when_wrapper_misses_done` 바로 위에 seq 613 verify_fsm output-close fallback 라운드에서 추가된 테스트라는 origin 주석을 추가했습니다.
- 테스트 본문, assertion, FSM 조건, enum 값, runtime 파일은 변경하지 않았습니다.

## 검증
- `python3 -m unittest tests.test_watcher_core`
  - `Ran 151 tests in 7.348s`
  - `OK`
- `git diff --check -- tests/test_watcher_core.py`
  - 출력 없음, `rc=0`

## 남은 리스크
- 이번 변경은 주석 truth-sync만 수행했으므로 watcher runtime 동작 자체의 추가 검증은 범위 밖으로 남아 있습니다.
- 전체 `python3 -m unittest -v`, pytest, Playwright smoke는 이번 handoff 범위에서 요구되지 않아 실행하지 않았습니다.
- 작업 시작 전부터 존재하던 unrelated dirty worktree 항목은 건드리지 않았습니다.
