# verify: 2026-05-22 verify_fsm export boundary clarification

## 검증 결과: READY — 275개 통과

| 검사 | 결과 |
|---|---|
| `py_compile` verify_fsm.py | PASS |
| `unittest` test_verify_fsm + test_watcher_core 275개 | PASS (9.0s) |
| export boundary smoke | OK |
| `git diff --check` | PASS |

## 명시된 __all__

```python
# verify_fsm이 직접 소유
"StateMachine", "make_job_id",
"compute_file_sig", "compute_md_tree_sig", "compute_multi_file_sig"

# watcher_state에서 하위 호환 re-export
"JobState", "JobStatus", "TERMINAL_STATES"
```

## 커밋 권장

```bash
git add verify_fsm.py tests/test_verify_fsm.py \
        work/5/22/2026-05-22-verify-fsm-export-boundary.md \
        verify/5/22/2026-05-22-verify-fsm-export-boundary.md
git commit -m "refactor(verify): add __all__ and re-export boundary comment to verify_fsm"
```
