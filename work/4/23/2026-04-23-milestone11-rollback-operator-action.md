# 2026-04-23 Milestone 11 rollback operator action

## 변경 파일

- `core/operator_executor.py`
- `tests/test_operator_executor.py`
- `work/4/23/2026-04-23-milestone11-rollback-operator-action.md`

## 사용 skill

- `approval-flow-audit`: rollback 함수가 새 approval/session flow를 만들지 않고, 기존 outcome record의 `backup_path`와 `target_id`를 입력으로 받는 실행 helper 범위인지 확인했습니다.
- `security-gate`: rollback이 로컬 파일 write-capable 동작이므로 backup 존재 확인, target 복원, missing-backup error branch를 확인했습니다.
- `finalize-lite`: handoff 지정 `py_compile`, 단위 테스트, diff check 결과만 근거로 구현 완료 여부를 정리했습니다.
- `work-log-closeout`: 변경 파일, 검증, 잔여 리스크를 `/work`에 기록했습니다.

## 변경 이유

`CONTROL_SEQ: 906` handoff의 Milestone 11 Axis 1 범위입니다. Milestone 10에서 reversible write backup과 `backup_path` audit trail은 마련됐지만, backup을 실제 `target_id`에 되돌리는 실행 함수가 없었습니다. 이번 변경은 `operator_action_history` outcome record를 입력으로 받아 원본 내용을 복원하는 `rollback_operator_action()` helper를 추가하는 것입니다.

## 핵심 변경

- `core/operator_executor.py`에 `rollback_operator_action(record: dict) -> dict`를 추가했습니다.
- rollback은 `local_file_edit`만 지원하며, 다른 action kind는 `ValueError`를 냅니다.
- `backup_path` 또는 `target_id`가 없으면 `ValueError`를 내고, backup 파일이 없으면 `restored=False`와 error payload를 반환합니다.
- backup 파일이 있으면 원본 내용을 읽어 `target_id`에 다시 쓰고 `restored=True`, `action_kind`, `target_id`, `backup_path`를 반환합니다.
- `tests/test_operator_executor.py`에 write-with-backup 후 rollback으로 원본이 복원되는 테스트와 missing-backup error branch 테스트를 추가했습니다.

## 검증

- `python3 -m py_compile core/operator_executor.py tests/test_operator_executor.py`
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit -v 2>&1 | tail -12`
  - 33개 테스트 통과
- `git diff --check -- core/operator_executor.py tests/test_operator_executor.py`

## 남은 리스크

- 이번 handoff는 helper와 unit tests만 지정했으므로 `agent_loop.py`, `session_store.py`, UI, docs는 변경하지 않았습니다.
- rollback 실행은 아직 approval route나 사용자-facing UI에 연결되지 않았습니다.
- sandbox path restriction, backup retention policy, rollback outcome audit 기록은 후속 Milestone 11 범위로 남아 있습니다.
