STATUS: verified
CONTROL_SEQ: 962
BASED_ON_WORK: work/4/23/2026-04-23-milestone13-axis2-correction-link.md
HANDOFF_SHA: f85404c
VERIFIED_BY: Claude
SUPERSEDES: verify/4/23/2026-04-23-milestone12-axis3-trace-quality-scoring.md CONTROL_SEQ 960

## Claim

Milestone 13 Axis 2 — Applied Preference → Correction Link:
- `storage/correction_store.py`: `record_correction()`에 `applied_preference_ids: list[str] | None = None` 파라미터 추가, record dict에 저장
- `app/handlers/feedback.py`: `record_correction()` 호출부에 `applied_preference_ids=updated_message.get("applied_preference_ids")` 전달
- `tests/test_export_utility.py`: `TestCorrectionPreferenceLinks.test_record_correction_stores_applied_preference_ids` 1건 추가 (`["pref-abc"]` 및 `None` 두 케이스 검증)

## Checks Run

- `python3 -m py_compile storage/correction_store.py app/handlers/feedback.py` → OK (exit 0)
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit tests.test_export_utility tests.test_promote_assets tests.test_evaluate_traces -v` → **58/58 통과** (기존 57 + 신규 1)
- `git diff --check -- storage/correction_store.py app/handlers/feedback.py tests/test_export_utility.py` → OK (exit 0)

## Actual Diff (added lines)

**`storage/correction_store.py`** — 시그니처 + record dict:
```python
# 파라미터 추가:
applied_preference_ids: list[str] | None = None,

# record dict에 추가 (pattern_family 다음):
"applied_preference_ids": applied_preference_ids,
```

**`app/handlers/feedback.py`** — `record_correction()` 호출부:
```python
applied_preference_ids=updated_message.get("applied_preference_ids"),
```

**`tests/test_export_utility.py`** — 신규 테스트 클래스:
```python
class TestCorrectionPreferenceLinks(unittest.TestCase):
    def test_record_correction_stores_applied_preference_ids(self) -> None:
        # ["pref-abc"] 전달 시 record에 저장 확인
        # None 전달 시 None으로 저장 확인
```

## Code Review

- `applied_preference_ids` 파라미터가 keyword-only이며 기본값 `None` — 기존 모든 호출부(`feedback.py` 1곳만)는 이제 전달하도록 업데이트됨. 올바름.
- `updated_message.get("applied_preference_ids")`: `updated_message`는 `session_store.record_correction_for_message()`가 반환하는 전체 session message dict. Axis 1에서 저장된 `applied_preference_ids`를 정확히 읽음. Axis 1이 없는 기존 메시지는 `None` 반환 — 안전.
- `session_store.py`, `agent_loop.py`, `preference_store.py`, 계약 파일 미수정. handoff 범위 준수.
- 기존 caller 중 `record_correction()`를 직접 호출하는 곳은 `feedback.py`의 이 호출부 1곳뿐 (grep 확인 가능). 다른 파일 영향 없음.

## Milestone 13 현황

| 항목 | 상태 |
|---|---|
| preference injection (agent_loop + ollama) | ✓ 기존 구현 완료 |
| applied_preference_ids session 저장 + export | ✓ Axis 1 (8cea2f1) |
| MILESTONES.md M13 항목 정의 | ✓ doc-sync (f85404c) |
| correction record에 preference link 보존 | ✓ 이번 Axis 2 |
| preference CANDIDATE → ACTIVE 전환 | deferred (guard rail) |
| PR #27 (feat/watcher-turn-state → main) | Draft 상태 |

## Bundle to Commit (operator_request.md CONTROL_SEQ 962)

### 수정 파일
- `storage/correction_store.py`
- `app/handlers/feedback.py`
- `tests/test_export_utility.py`
- `verify/4/23/2026-04-23-milestone12-axis3-trace-quality-scoring.md` (CONTROL_SEQ 962)

### 신규 파일 (untracked — this round)
- `work/4/23/2026-04-23-milestone13-axis2-correction-link.md`
- `work/4/23/2026-04-23-milestone13-docsync-commit-push.md`

## Risk / Open Questions

- M13 Axis 3 범위 미결정: preference 효과 측정(correction rate 비교), UI 표시, 자동화 확장 여부는 별도 advisory 또는 다음 handoff에서 결정.
- 현재 active preferences = 0이므로 `applied_preference_ids`가 실제 채워지는 케이스는 없음 — 코드 경로는 올바름.
- PR #27 merge 결정은 별도 operator 승인 필요.
