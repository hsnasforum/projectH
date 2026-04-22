# 2026-04-23 Milestone 10 local_file_edit backup

## 변경 파일

- `core/contracts.py`
- `core/operator_executor.py`
- `core/agent_loop.py`
- `tests/test_operator_executor.py`
- `work/4/23/2026-04-23-milestone10-local-file-edit-backup.md`

## 사용 skill

- `approval-flow-audit`: backup 생성은 기존 operator action pending approval 승인 후 실행 경로에만 붙고, 승인 전 write 경로를 새로 만들지 않는지 확인했습니다.
- `security-gate`: 실제 파일 overwrite 전에 reversible backup을 남기는 write-capable 안전 경계를 점검했습니다.
- `finalize-lite`: handoff 지정 `py_compile`, 단위 테스트, diff check 결과만 근거로 구현 완료 여부를 정리했습니다.
- `work-log-closeout`: 변경 파일, 검증, 잔여 리스크를 `/work`에 기록했습니다.

## 변경 이유

`CONTROL_SEQ: 896` handoff의 Milestone 10 Axis 2 범위입니다. Axis 1에서 `local_file_edit`가 `content`를 실제 파일에 쓰도록 열렸지만, 기존 파일을 덮어쓸 때 복원 가능한 backup 경로가 없었습니다. 이번 변경은 `is_reversible=True`이고 대상 파일이 이미 있을 때 원본을 `backup/operator/` 아래에 저장하고 그 경로를 outcome으로 남기는 것입니다.

## 핵심 변경

- `OperatorActionRecord`에 execution-time result 필드인 optional `backup_path`를 추가했습니다.
- `execute_operator_action()`의 write branch에서 `is_reversible=True`이고 대상 파일이 존재하면 `backup/operator/<stem>_<timestamp><suffix>`에 기존 내용을 저장합니다.
- write 결과에 `backup_path`를 포함하고, `agent_loop.py`가 이를 `operator_action_history` outcome record로 전달하도록 했습니다.
- `is_reversible=False`이거나 기존 파일이 없으면 backup을 만들지 않고 기존 write 동작을 유지합니다.
- `tests/test_operator_executor.py`에 reversible backup 생성 테스트와 non-reversible no-backup 테스트를 추가했습니다.

## 검증

- `python3 -m py_compile core/contracts.py core/operator_executor.py core/agent_loop.py tests/test_operator_executor.py`
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader -v 2>&1 | tail -12`
  - 30개 테스트 통과
- `git diff --check -- core/contracts.py core/operator_executor.py core/agent_loop.py tests/test_operator_executor.py`

## 남은 리스크

- backup 파일을 실제로 복원하는 rollback command는 이번 handoff 범위가 아니어서 추가하지 않았습니다.
- backup 위치는 현재 handoff 지정대로 repo 상대 `backup/operator/`입니다. 경로 제한, 저장 위치 정책, retention 정책은 후속 정리가 필요합니다.
- 문서 동기화와 브라우저/Playwright 검증은 이번 handoff 범위가 아니어서 실행하지 않았습니다.
- `shell_execute`와 `session_mutation`은 계속 지원하지 않는 action kind로 남아 있습니다.
