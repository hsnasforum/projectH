STATUS: verified
CONTROL_SEQ: 875
BASED_ON_WORK: work/4/23/2026-04-23-milestone9-execution-stub.md
HANDOFF_SHA: e286eb3
VERIFIED_BY: Claude

## Claim

Milestone 9 Axis 3 — Minimal Execution Stub:
- `core/operator_executor.py` (신규): `execute_operator_action(record) -> dict` — LOCAL_FILE_EDIT 10줄 preview, 기타 kind는 ValueError
- `core/agent_loop.py` 최소 편집: `ApprovalKind` + `execute_operator_action` import 추가, `_execute_pending_approval` 내 operator_action 분기 삽입
- `tests/test_operator_executor.py` (신규): 4개 테스트

## Checks Run

- `python3 -m py_compile core/operator_executor.py core/agent_loop.py` → OK
- `git diff --check -- core/operator_executor.py core/agent_loop.py tests/test_operator_executor.py` → OK
- `python3 -m unittest tests.test_operator_executor -v` → 4/4 통과
- `python3 -m unittest tests.test_session_store tests.test_eval_loader -v` → 21/21 통과 (zero regression)

## Code Review

### `core/operator_executor.py`
- `execute_operator_action(record: dict) -> dict` — 단일 책임, 28줄.
- `action_kind != OperatorActionKind.LOCAL_FILE_EDIT` → ValueError. 올바름.
- `target_id` 빈 값 → ValueError. 올바름.
- 파일 미존재 → 오류 문자열 preview dict 반환. 올바름.
- `path.read_text(encoding="utf-8", errors="replace").splitlines()[:10]` — read-only, 쓰기 없음. 올바름.

### `core/agent_loop.py`
- `ApprovalKind` import 추가 (line 18): `from core.contracts import (... ApprovalKind ...)`. 올바름.
- `from core.operator_executor import execute_operator_action` (line 34): 모듈 레벨 import. 올바름.
- `_execute_pending_approval` 내 삽입 위치 (line 7500–7513): `pop_pending_approval` None 체크 직후, `ApprovalRequest.from_record()` 호출 직전. 올바름 — save_note 경로 미변경.
- ValueError catch → `ResponseStatus.ERROR` + `approval_error`. 올바름.
- 성공 → `ResponseStatus.SAVED` + `["approval_granted", "operator_action_executed"]`. 올바름.
- 기존 `if approval.kind != "save_note"` guard (line 7516) 유지됨 — 다른 unknown kind에 대한 방어. 올바름.

### 보안 검토
- `execute_operator_action`은 순수 read-only: `path.read_text()`만 사용. 파일 쓰기 없음.
- `shell_execute`, `session_mutation`은 명시적 ValueError로 거절됨. 실행 경로 없음.
- `pop_pending_approval` 먼저 호출 후 실행 — ValueError 시 레코드 소멸. save_note와 동일한 패턴으로 허용 가능.

### `tests/test_operator_executor.py`
- `test_local_file_edit_returns_preview`: 15줄 파일 → preview 10줄 검증. 올바름.
- `test_unsupported_kind_raises`: `shell_execute` → ValueError. 올바름.
- `test_missing_target_id_raises`: 빈 target_id → ValueError. 올바름.
- `test_missing_file_returns_not_found`: 존재하지 않는 경로 → preview에 "파일 없음" 포함. 올바름.

## Risk / Open Questions

- No regression on 21 existing tests (12 session_store + 9 eval_loader).
- operator_action record는 실행 전 pop됨 — 실행 실패 시 레코드 미보존. 현재 단계에서 허용. outcome 저장은 별도 슬라이스.
- 실제 파일 쓰기, rollback, UI approval card, MILESTONES.md 동기화는 이번 handoff 범위 밖 — 다음 슬라이스 판단 필요.
