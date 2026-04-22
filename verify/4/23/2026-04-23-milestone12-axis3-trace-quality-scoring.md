STATUS: verified
CONTROL_SEQ: 958
BASED_ON_WORK: work/4/23/2026-04-23-milestone13-axis1-applied-preference-tracking.md
HANDOFF_SHA: 32f9d39
VERIFIED_BY: Claude
SUPERSEDES: verify/4/23/2026-04-23-milestone12-axis3-trace-quality-scoring.md CONTROL_SEQ 946

## Claim

Milestone 13 Axis 1 — Applied Preference Tracking:
- `app/handlers/chat.py`: `_handle_chat_impl()` `update_last_message()` 호출에 `applied_preference_ids` 추가 (response.applied_preferences가 있을 때만)
- `storage/session_store.py`: `stream_trace_pairs()` yield에 `"applied_preference_ids": msg.get("applied_preference_ids")` 추가
- `tests/test_export_utility.py`: `test_stream_trace_pairs_includes_applied_preference_ids_key` 1건 추가 (key 존재 + None 확인)

## Checks Run

- `python3 -m py_compile app/handlers/chat.py storage/session_store.py tests/test_export_utility.py` → OK (exit 0)
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit tests.test_export_utility tests.test_promote_assets tests.test_evaluate_traces -v` → **57/57 통과** (기존 56 + 신규 1)
- `git diff --check -- app/handlers/chat.py storage/session_store.py tests/test_export_utility.py` → OK (exit 0)

## Actual Diff (added lines)

**`app/handlers/chat.py`** — `update_last_message()` 호출에 추가:
```python
**(
    {"applied_preference_ids": [p["fingerprint"] for p in response.applied_preferences]}
    if response.applied_preferences
    else {}
),
```

**`storage/session_store.py`** — `stream_trace_pairs()` yield에 추가:
```python
"applied_preference_ids": msg.get("applied_preference_ids"),
```

**`tests/test_export_utility.py`** — 신규 테스트 1건:
```python
def test_stream_trace_pairs_includes_applied_preference_ids_key(self) -> None:
    # key 존재 + None (preferences 미적용 시) 검증
```

## Code Review

- `response.applied_preferences`가 `None`이면 `update_last_message()` payload에 키 자체가 포함되지 않음 — 기존 필드 간섭 없음. 올바름.
- `msg.get("applied_preference_ids")` → 기존 메시지에 해당 키 없으면 `None` 반환 — M12 Axis 6의 `feedback` 필드와 동일 패턴. 올바름.
- `preference_store.py`, `correction_store.py`, `agent_loop.py`, 계약 파일 미수정. handoff 범위 준수.
- 현재 active preferences = 0 → `applied_preference_ids`가 세팅되는 케이스는 없지만 코드 경로는 올바름.

## Milestone 13 현황

| 항목 | 상태 |
|---|---|
| preference injection (agent_loop + ollama) | ✓ 기존 구현 완료 |
| applied_preference_ids session 저장 + export | ✓ 이번 Axis 1 |
| preference CANDIDATE → ACTIVE 전환 | deferred (guard rail) |
| PR #27 (feat/watcher-turn-state → main) | Draft 상태 |

## Bundle to Commit (operator_request.md CONTROL_SEQ 958)

### 수정 파일
- `app/handlers/chat.py`
- `storage/session_store.py`
- `tests/test_export_utility.py`

### 신규 파일 (untracked — this round)
- `work/4/23/2026-04-23-milestone13-axis1-applied-preference-tracking.md`

### 기존 미커밋 untracked (이전 rounds 산출물 — 함께 번들 가능)
- `work/4/23/2026-04-23-milestone12-docsync-close-commit-push.md`
- `work/4/23/2026-04-23-pr27-draft-create.md`
- `report/gemini/2026-04-23-*.md` (5개 advisory 보고서)

## Risk / Open Questions

- active preferences = 0이므로 `applied_preference_ids`는 현재 항상 None. 실제 효과는 preference 활성화 이후.
- MILESTONES.md에 M13이 아직 정의되지 않음 — doc-sync 필요 (별도 bounded 라운드).
- PR #27 merge 결정은 별도 operator 승인 필요.
