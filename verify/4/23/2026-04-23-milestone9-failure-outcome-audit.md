STATUS: verified
CONTROL_SEQ: 883
BASED_ON_WORK: work/4/23/2026-04-23-milestone9-failure-outcome-audit.md
HANDOFF_SHA: 1aba2eb
VERIFIED_BY: Claude

## Claim

Milestone 9 Axis 5 (final) — Failure Outcome Audit:
- `core/agent_loop.py`: `_execute_pending_approval` ValueError 경로에 실패 outcome 기록 삽입
- `tests/test_session_store.py`: `test_operator_action_failed_outcome_preserved` 추가

## Checks Run

- `python3 -m py_compile core/agent_loop.py` → OK
- `git diff --check -- core/agent_loop.py tests/test_session_store.py` → OK
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader -v` → 27/27 통과 (zero regression)

## Code Review

### `core/agent_loop.py` (line 7503–7514)

`except ValueError as exc:` 블록 — 현재 상태:
```python
            except ValueError as exc:
                outcome_record = dict(approval_record)
                outcome_record["status"] = "failed"
                outcome_record["error"] = str(exc)
                self.session_store.record_operator_action_outcome(
                    request.session_id, outcome_record
                )
                return AgentResponse(
                    text=f"작업 실행 실패: {exc}",
                    status=ResponseStatus.ERROR,
                    actions_taken=["approval_error"],
                )
```

- `dict(approval_record)` 복사 후 `status="failed"`, `error=str(exc)` 설정. 올바름.
- `record_operator_action_outcome` 호출 후 기존 `AgentResponse` 반환. 올바름.
- `record_operator_action_outcome`의 `setdefault("status", "executed")`는 `status="failed"`가 이미 있으면 덮어쓰지 않음 — 확인 완료.
- 성공 경로 (line 7515–7524): 미변경. 올바름.
- save_note 경로 (line 7525+): 미변경. 올바름.

### `tests/test_session_store.py`
- `test_operator_action_failed_outcome_preserved`: `record_operator_action_outcome`에 `status="failed"` + `error` 직접 전달 → `get_session` → history[0] 검증. `status`, `error`, `completed_at` 모두 확인. 디스크 round-trip 포함. 올바름.

## Milestone 9 Axes 1–5 완료 상태

| Axis | seq | 내용 |
|---|---|---|
| 1 | 866 | `OperatorActionKind` + `OperatorActionContract` data contract |
| 2 | 871 | `OperatorActionRecord` + `ApprovalKind.OPERATOR_ACTION` + `record_operator_action_request()` |
| 3 | 875 | `execute_operator_action()` read-only stub + agent_loop 분기 |
| 4 | 879 | `operator_action_history` + `record_operator_action_outcome()` + 성공 outcome wire-up |
| 5 | 883 | 실패 outcome 기록 — audit trail 완결 |

## Risk / Open Questions

- 27개 테스트 전부 통과. zero regression.
- Gemini advisory 881: "This is the final implementation slice before Milestone 9 doc-sync." — Axes 1–5 shipped 기록 + Milestone 9 close 판단은 advisory 위임.
- rollback 처리, UI approval card, shell/session mutation 실행은 이번 milestone 범위 밖으로 명시적 deferred 상태.
- MILESTONES.md Axis 5 기록 아직 없음 — operator_retriage 커밋 시 인라인 추가 필요.
