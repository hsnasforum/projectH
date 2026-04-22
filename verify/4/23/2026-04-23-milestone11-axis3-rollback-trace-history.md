STATUS: verified
CONTROL_SEQ: 916
BASED_ON_WORK: work/4/23/2026-04-23-milestone11-axis3-rollback-trace-history.md
HANDOFF_SHA: 5939a5d
VERIFIED_BY: Claude

## Claim

Milestone 11 Axis 3 — rollback traces observable in session history:
- `UserRequest`에 `rollback_approval_id: str | None = None` 추가 (line 70)
- `_execute_operator_rollback(request)` 메서드 추가 (lines 7590–7629)
- `_handle_approval_flow` dispatch에 `rollback_execute` 분기 추가 (lines 7961–7969)
- `storage/session_store.py`에 `get_operator_action_from_history(session_id, approval_id)` 추가 (lines 1636–1644)
- `tests/test_operator_audit.py`에 `test_rollback_trace_in_history` 추가

## Checks Run

- `python3 -m py_compile core/agent_loop.py storage/session_store.py tests/test_operator_audit.py` → OK
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit -v` → **36/36 통과** (기존 35 + 신규 1)
- `git diff --check -- core/agent_loop.py storage/session_store.py tests/test_operator_audit.py` → OK

## Code Review

### `core/agent_loop.py`

- `rollback_approval_id: str | None = None` (line 70): `reissue_approval_id` 직후 삽입. 기본값 None으로 기존 callsite 무영향. 올바름.
- `_execute_operator_rollback` (lines 7590–7629):
  - `approval_id` 비어 있음 → error AgentResponse. 올바름.
  - `get_operator_action_from_history` 로 history 조회 → None이면 error AgentResponse. 올바름.
  - `rollback_operator_action(record)` 호출 → `outcome["status"] = "rolled_back"` 명시적 설정. 올바름.
  - `record_operator_action_outcome` 은 `setdefault("status", "executed")` 이므로 "rolled_back" 보존됨. 올바름.
  - `restored=False` 분기 → error AgentResponse; `restored=True` → SAVED AgentResponse. 올바름.
- Dispatch (lines 7961–7969): `rejected` 분기 직후, `return None` 직전. 기존 execute/reissue/rejected 흐름 미변경. 올바름.

### `storage/session_store.py`

- `get_operator_action_from_history` (lines 1636–1644):
  - `self._lock` 사용 — thread-safe. 올바름.
  - `entry.get("approval_id") == approval_id` 선형 탐색. history가 크지 않으므로 적합.
  - `dict(entry)` 복사 반환 — 내부 참조 노출 없음. 올바름.

### `tests/test_operator_audit.py` — `test_rollback_trace_in_history`

- `TemporaryDirectory` + `NamedTemporaryFile(dir=".")` — 격리 + CWD sandbox 준수. 올바름.
- execute → `record_operator_action_outcome(status="executed")` → `get_operator_action_from_history` → `rollback_operator_action` → `record_operator_action_outcome(status="rolled_back")` 전체 사이클 검증.
- `history[0]["status"] == "executed"`, `history[1]["status"] == "rolled_back"`, `history[1]["restored"] == True` 어서션. 올바름.
- `finally` cleanup: target + backup 파일 조건부 삭제. 올바름.

## Risk / Open Questions

- `_execute_operator_rollback`에서 `rollback_operator_action` 이 `ValueError` (sandbox 위반 등)를 raise하는 경우 현재 catch 없음 — 상위 exception handler가 처리해야 함.
- rollback trigger를 프론트엔드/route에서 `rollback_approval_id` 로 전달하는 경로 미구현 — UI 연결은 별도 슬라이스.
- backup 파일 보존/삭제 정책, backup_path sandbox 검증 미적용 — 별도 정책 결정 필요.
- 브라우저/Playwright 미실행: frontend 변경 없음.
- Milestone 11 모든 축 구현 완료 (Axis 1, 2, 3). 문서 sync 미완.
