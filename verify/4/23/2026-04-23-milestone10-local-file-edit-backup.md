STATUS: verified
CONTROL_SEQ: 897
BASED_ON_WORK: work/4/23/2026-04-23-milestone10-local-file-edit-backup.md
HANDOFF_SHA: da0e280
VERIFIED_BY: Claude

## Claim

Milestone 10 Axis 2 — `local_file_edit` backup on reversible write:
- `OperatorActionRecord`에 optional `backup_path: str` 추가 (OperatorActionContract에는 추가 안 함)
- `execute_operator_action()`: `is_reversible=True` + 대상 파일 존재 시 `backup/operator/<stem>_<timestamp><suffix>` 백업 후 쓰기
- `agent_loop.py`: executor result의 `backup_path`를 outcome_record에 조건부 보존
- 신규 테스트 2개: reversible 백업 생성 확인, non-reversible 백업 없음 확인

## Checks Run

- `python3 -m py_compile core/contracts.py core/operator_executor.py core/agent_loop.py tests/test_operator_executor.py` → OK
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader -v` → **30/30 통과** (기존 28 + 신규 2)
- `git diff --check -- core/contracts.py core/operator_executor.py core/agent_loop.py tests/test_operator_executor.py` → OK

## Code Review

### `core/contracts.py` (line 327)

- `backup_path: str` — `OperatorActionRecord`에만 추가, `OperatorActionContract`에는 없음. 실행 시점 결과 필드이므로 올바름.

### `core/operator_executor.py` (55 lines)

- `from datetime import datetime` import (line 3): 올바름.
- `is_reversible = bool(record.get("is_reversible"))` (line 20): None → False 안전 변환. 올바름.
- `backup_path: str | None = None` (line 21): 조건부 초기화. 올바름.
- `if is_reversible and path.exists()` (line 22): reversible이고 파일 존재 시에만 백업. 신규 파일 생성 케이스(덮어쓸 파일 없음) 올바르게 제외.
- `backup_dir.mkdir(parents=True, exist_ok=True)` (line 24): 반복 실행 안전. 올바름.
- 타임스탬프 `%Y%m%d_%H%M%S_%f` (line 25): 마이크로초 정밀도, 충돌 확률 극히 낮음. 올바름.
- 원본 읽기(`errors="replace"`) → 백업 저장 → 이후 쓰기 (lines 28–32): **순서 중요** — 백업 먼저, 덮어쓰기 나중. 올바름.
- `if backup_path is not None: result["backup_path"] = backup_path` (lines 40–41): None이면 key 자체 없음. 올바름.

### `core/agent_loop.py` (lines 7518–7519)

- `if "backup_path" in result: outcome_record["backup_path"] = result["backup_path"]`: preview 설정과 `record_operator_action_outcome` 호출 사이에 위치. 조건부라 backup 없는 케이스에 영향 없음. 올바름.

### `tests/test_operator_executor.py` (lines 44–84)

- `test_local_file_edit_backup_on_reversible_write`:
  - `backup_path = None` 초기화 후 finally에서 검사 — `backup_path` 미설정 시에도 unlink 시도 안 함. 올바름.
  - 백업 파일 내용 `"original backup test"` 직접 읽어 검증. 올바름.
  - 대상 파일 내용 `"new content"` 검증. 올바름.
  - `finally` 블록에서 temp file + backup file 정리. 올바름.
- `test_local_file_edit_no_backup_when_not_reversible`:
  - `assertNotIn("backup_path", result)` — is_reversible=False 케이스 회귀 방어. 올바름.
- 기존 5개 테스트 (`test_local_file_edit_returns_preview`, `test_local_file_edit_writes_to_disk`, `test_unsupported_kind_raises`, `test_missing_target_id_raises`, `test_missing_file_returns_not_found`) 전원 통과 — 하위 호환 확인.

## Risk / Open Questions

- `backup/operator/` 경로는 프로세스 CWD 기준 상대 경로. CI나 다른 CWD 환경에서 예상치 못한 위치에 생성 가능. 경로 정책은 후속 범위.
- backup 파일 retention/cleanup 정책 미정의. 무한 축적 가능. 후속 범위.
- backup에서 실제 복원 실행(rollback command)은 미구현 — Axis 3 범위.
- `_normalize_operator_action_record`에 `backup_path` 미포함 — 그러나 backup_path는 pending_approvals가 아닌 operator_action_history outcome에만 기록되므로 정규화 경로에 영향 없음. 안전.
- 브라우저/Playwright 미실행: frontend 변경 없음.
