STATUS: verified
CONTROL_SEQ: 871
BASED_ON_WORK: work/4/23/2026-04-23-milestone9-storage-approval-wiring.md
HANDOFF_SHA: cae65a4
VERIFIED_BY: Claude

## Claim

Milestone 9 Axis 2 — Storage & Approval Wiring:
- `OperatorActionRecord` TypedDict + `ApprovalKind.OPERATOR_ACTION` added to `core/contracts.py`
- `record_operator_action_request()` + `_normalize_operator_action_record()` + `_normalize_pending_approval_record()` added to `storage/session_store.py`
- `test_operator_action_request_round_trip` added to `tests/test_session_store.py`

## Checks Run

- `python3 -m py_compile core/contracts.py storage/session_store.py` → OK
- `git diff --check -- core/contracts.py storage/session_store.py tests/test_session_store.py` → OK
- `python3 -m unittest tests.test_session_store tests.test_eval_loader -v` → 21 tests, 0 failures

## Code Review

### `core/contracts.py`
- `OperatorActionRecord` (line 316): 7 fields, total=False — 5 inherited from OperatorActionContract + `approval_id: str`, `status: str`, `outcome_id: str`. Correct.
- `ApprovalKind.OPERATOR_ACTION = "operator_action"` (line 396) added alongside `SAVE_NOTE`. Correct.

### `storage/session_store.py`
- `_normalize_operator_action_record` (line 158): validates `approval_id`, `kind == "operator_action"`, `status` presence; preserves all 6 optional OperatorAction fields. Correct.
- `_normalize_pending_approval_record` (line 181): routes `operator_action` kind to new normalizer, all other kinds to original `_normalize_approval_record`. Used in `_normalize_session` at line 853. Correct — this ensures operator_action records survive session reload (old normalizer requires `requested_path` and would drop them).
- `record_operator_action_request` (line 1599): generates uuid4 approval_id, builds raw record with `kind="operator_action"`, `status="pending"`, copies OperatorActionContract fields; acquires `RLock` then calls `get_session` → safe (RLock is re-entrant); appends raw without going through `_normalize_approval_record`. Correct.
- `add_pending_approval` (line 1583): unchanged — still routes through `_normalize_approval_record` for save-note approvals. Correct separation.

### `tests/test_session_store.py`
- `test_operator_action_request_round_trip` (line 70): calls `record_operator_action_request`, asserts non-empty approval_id string, fetches via `get_pending_approval`, asserts `kind == "operator_action"`, `status == "pending"`, `action_kind == "local_file_edit"`. Round-trip is through disk (get_session always reads from disk → no in-memory cache). Correct.

## Risk / Open Questions

- No regression on existing 11 session_store tests or 9 eval_loader tests.
- `_normalize_pending_approval_record` is a new routing point in the session normalization path — callers of `add_pending_approval` that expected to use the old `_normalize_approval_record` path are unaffected (add_pending_approval unchanged).
- Still deferred: approval gate check before action dispatch, outcome/rollback processing, UI surface for operator action approvals.
- MILESTONES.md not updated in implement round — to be bundled inline in commit.
