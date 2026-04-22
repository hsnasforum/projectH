# 2026-04-23 Milestone 11 Axis 3 rollback trace history

## 변경 파일
- `core/agent_loop.py`
- `storage/session_store.py`
- `tests/test_operator_audit.py`
- `work/4/23/2026-04-23-milestone11-axis3-rollback-trace-history.md`

## 사용 skill
- `approval-flow-audit`: rollback dispatch가 기존 승인 실행/거절/재발급 흐름을 바꾸지 않고 history 기반 후속 기록만 추가하는지 확인했습니다.
- `security-gate`: rollback이 로컬 파일 복원과 session history 기록을 동반하므로 실행 대상, audit 기록, 남은 rollback 리스크를 점검했습니다.
- `finalize-lite`: handoff가 요구한 세 파일 변경과 지정 검증 결과만 기준으로 구현 완료 여부를 정리했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 명령, 남은 리스크를 한국어 `/work` closeout으로 남겼습니다.

## 변경 이유
- Milestone 11 Axis 3 handoff(`CONTROL_SEQ: 915`)에 따라 `rollback_approval_id` 기반 rollback 실행 결과가 `operator_action_history`에서 관찰 가능해야 했습니다.
- frontend, approval-flow, session schema는 변경하지 않고 기존 history record를 조회해 rollback outcome을 append하는 범위로 제한했습니다.

## 핵심 변경
- `core/agent_loop.py`의 `UserRequest`에 `rollback_approval_id`를 추가하고 `_handle_approval_flow`에 `rollback_execute` dispatch 분기를 추가했습니다.
- `_execute_operator_rollback`을 추가해 기존 `operator_action_history` record를 조회하고 `rollback_operator_action` 결과를 `status="rolled_back"` outcome으로 기록하도록 했습니다.
- `storage/session_store.py`에 `get_operator_action_from_history(session_id, approval_id)` helper를 추가했습니다.
- `tests/test_operator_audit.py`에 execute → history 조회 → rollback → rolled_back outcome append까지 검증하는 `test_rollback_trace_in_history`를 추가했습니다.

## 검증
- `python3 -m py_compile core/agent_loop.py storage/session_store.py tests/test_operator_audit.py`
  - 통과
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit -v 2>&1 | tail -14`
  - `Ran 36 tests in 0.041s`
  - `OK`

## 남은 리스크
- 이번 slice는 agent loop dispatch와 storage/history trace만 다뤘습니다. frontend rollback trigger, approval-card UI, route-level payload 전달은 handoff 범위가 아니어서 수정하지 않았습니다.
- `rollback_operator_action`의 `ValueError` 표면화는 별도 UX/route 처리 없이 현재 helper 예외 동작을 따릅니다.
- rollback 후 backup 파일 보존/삭제 정책과 backup_path 자체 sandbox 정책은 아직 별도 정책으로 남아 있습니다.
