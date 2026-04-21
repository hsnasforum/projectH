# 2026-04-21 verify output close fallback

## 변경 파일
- `.pipeline/README.md`
- `verify_fsm.py`
- `tests/test_watcher_core.py`
- `work/4/21/2026-04-21-verify-output-close-fallback.md`

## 사용 skill
- `security-gate`: runtime control/log close fallback이 approval 기록, 사용자 문서 쓰기, 외부 네트워크, 삭제/덮어쓰기 동작을 새로 만들지 않는지 점검했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 표준 Korean closeout 형식으로 정리했습니다.

## 변경 이유
- 이번 정지는 다음 작업 부재가 아니라 verify lane wrapper의 `TASK_DONE` 신호가 누락된 상태에서 `/verify` 기록과 다음 control slot이 이미 만들어졌는데도 FSM이 완료를 닫지 못한 생산성 문제였습니다.
- 같은 유형이 반복되면 사람이 수동으로 pane을 깨워야 하므로, 산출물과 lane idle 상태가 충분히 확인된 경우에만 완료를 추론하는 좁은 fallback을 추가했습니다.

## 핵심 변경
- `verify_fsm.py`에 `_mark_task_done_from_completed_outputs(...)`를 추가해, 현재 dispatch의 `/verify` receipt와 다음 control close가 완료되고 lane이 idle이며 done deadline이 지난 경우에만 누락된 `TASK_DONE`을 추론합니다.
- 기존 stall/requeue/degraded 경로는 busy lane 또는 산출물 미완료 상태에는 그대로 유지했습니다.
- 추론 close는 job history와 warning log에 `inferred TASK_DONE` 이유를 남겨, 나중에 wrapper 신호 누락과 fallback close를 구분할 수 있게 했습니다.
- `tests/test_watcher_core.py`에 wrapper `TASK_DONE` 없이 `/verify`와 next handoff가 완성된 idle lane을 `VERIFY_DONE`으로 닫는 회귀 테스트를 추가했습니다.
- `.pipeline/README.md`의 runtime contract에 이 fallback 조건과 비적용 조건을 문서화했습니다.

## 검증
- `python3 -m py_compile verify_fsm.py watcher_core.py`
  - 출력 없음, `rc=0`
- `python3 -m unittest tests.test_watcher_core.VerifyCompletionContractTest`
  - `Ran 20 tests in 0.305s`
  - `OK`
- `git diff --check -- verify_fsm.py tests/test_watcher_core.py .pipeline/README.md`
  - 출력 없음, `rc=0`
- `python3 -m unittest tests.test_watcher_core`
  - `Ran 151 tests in 7.749s`
  - `OK`

## 남은 리스크
- wrapper가 `TASK_DONE`을 누락하는 근본 원인은 이번 slice에서 직접 수정하지 않았습니다. 이번 변경은 current-round receipt, next control, idle lane, done deadline 이후에만 작동하는 방어적 fallback입니다.
- 전체 `python3 -m pytest -q`와 Playwright 전체 smoke는 이번 좁은 FSM 변경 뒤에 다시 돌리지 않았습니다.
- 작업 시작 전부터 있던 unrelated dirty worktree 항목과 진행 중인 automation/Gemini 산출물은 건드리지 않았습니다.
- 이 slice는 아직 commit/push하지 않았습니다.
