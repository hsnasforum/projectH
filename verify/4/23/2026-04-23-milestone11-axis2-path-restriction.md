STATUS: verified
CONTROL_SEQ: 912
BASED_ON_WORK: work/4/23/2026-04-23-milestone11-axis2-path-restriction.md
HANDOFF_SHA: 3c2f710
VERIFIED_BY: Claude

## Claim

Milestone 11 Axis 2 — `target_id` path restriction (sandbox):
- `core/operator_executor.py`에 `_validate_operator_action_target(target_id)` 추가
- `execute_operator_action` + `rollback_operator_action` 양쪽에서 `target_id` 비어 있음 검증 직후 호출
- `Path(target_id).resolve().is_relative_to(Path.cwd().resolve())` 실패 시 `ValueError` 발생
- `tests/test_operator_executor.py`: `NamedTemporaryFile` 5곳 `dir="."` 적용, missing-file/missing-backup 테스트 CWD 상대경로로 교체, 신규 path restriction 테스트 2건 추가
- `tests/test_operator_audit.py`: `NamedTemporaryFile` 1곳 `dir="."` 적용

## Checks Run

- `python3 -m py_compile core/operator_executor.py tests/test_operator_executor.py tests/test_operator_audit.py` → OK
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit -v` → **35/35 통과** (기존 33 + 신규 2)
- `git diff --check -- core/operator_executor.py tests/test_operator_executor.py tests/test_operator_audit.py` → OK

## Code Review

### `core/operator_executor.py`

- `_validate_operator_action_target` (lines 9–13):
  - `Path(target_id).resolve()` + `Path.cwd().resolve()` — symlink 해결 포함한 정규화. 올바름.
  - `.is_relative_to(cwd)` — Python 3.9+ 정적 비교. 올바름.
  - `ValueError` 발생 — not_found soft-fail이 아닌 hard guard. 올바름.
- `execute_operator_action` (line 23): `target_id` 비어 있음 검증 직후, `path = Path(target_id)` 이전에 호출. 올바름.
- `rollback_operator_action` (line 75): `target_id` 비어 있음 검증 직후, `backup = Path(backup_path)` 이전에 호출. 올바름.

### `tests/test_operator_executor.py`

- `from pathlib import Path` import 추가 (line 3). 올바름.
- `NamedTemporaryFile(mode="w", suffix=".txt", dir=".", delete=False)` — 5개 모두 `dir="."`. 올바름.
- `test_missing_file_returns_not_found`: `str(Path.cwd() / "nonexistent_test_file_verify_xyz.txt")` — CWD 내부 nonexistent path. 올바름.
- `test_rollback_missing_backup_returns_error`: `Path.cwd() / "nonexistent_*.txt"` — sandbox 통과하는 경로. 올바름.
- `test_local_file_edit_path_restriction`: `/etc/passwd` → `ValueError` assertRaises. 올바름.
- `test_rollback_path_restriction`: `/etc/passwd` target → `ValueError` assertRaises; backup은 CWD 내 경로. 올바름.
- `test_unsupported_kind_raises` (line 129): `/tmp/x` target 사용하지만 action_kind 검증이 먼저 발생 — sandbox guard 미도달이나 ValueError 발생 보장. 회귀 없음.

### `tests/test_operator_audit.py` (line 14)

- `NamedTemporaryFile(mode="w", suffix=".txt", dir=".", delete=False)` — CWD 내부 생성. 올바름.

## Risk / Open Questions

- sandbox는 `execute_operator_action` / `rollback_operator_action` 진입 시 강제되나, agent_loop approval dispatch 이전 단계(record_operator_action_request 시점)에는 경로 검증 없음.
- rollback `backup_path` 자체는 sandbox 검증 대상에서 제외 — backup 디렉터리는 `backup/operator/` CWD 내 경로라 실질적 위험 낮음.
- Milestone 11 Axis 3 (rollback trace → session history) 미구현.
- 브라우저/Playwright 미실행: frontend 변경 없음.
