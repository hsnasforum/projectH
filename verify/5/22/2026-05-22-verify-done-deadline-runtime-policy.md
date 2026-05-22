# verify: 2026-05-22 verify done deadline runtime policy (2129)

## 대상 work
`work/5/22/2026-05-22-verify-done-deadline-runtime-policy.md`

## 검증 결과: READY

---

## 코드 확인

| 항목 | 위치 | 확인 |
|---|---|---|
| `DEFAULT_VERIFY_DONE_DEADLINE_SEC = 300.0` 상수 추가 | `watcher_core.py:246` | ✓ |
| `config.get("verify_done_deadline_sec", DEFAULT_VERIFY_DONE_DEADLINE_SEC)` | `watcher_core.py:609-610` (45.0 → 상수) | ✓ |
| `--verify-done-deadline` CLI 플래그 추가 (default=300.0) | `watcher_core.py` main() | ✓ |
| `verify_done_deadline_sec` config dict에 주입 | `watcher_core.py` main() | ✓ |
| `_DEFAULT_VERIFY_DONE_DEADLINE_SEC = 300.0` 상수 추가 | `supervisor.py:130` | ✓ |
| `_verify_done_deadline_sec()` 메서드 — runtime_policy.json 읽기 | `supervisor.py` | ✓ |
| `--verify-done-deadline` watcher_args 전달 | `supervisor.py _watcher_shell_command()` | ✓ |
| `"verify_done_deadline_sec": 300` | `.pipeline/config/runtime_policy.json` | ✓ |

## 회귀 테스트

| 검사 | 결과 |
|---|---|
| `py_compile` watcher_core.py / supervisor.py | PASS |
| `test_default_verify_done_deadline_is_300_seconds` | PASS |
| `test_watcher_shell_command_passes_verify_done_deadline_from_runtime_policy` | PASS |
| `tests.test_watcher_core` 전체 (265개 포함) | PASS (487개 OK) |
| `tests.test_pipeline_runtime_supervisor` 전체 (222개 포함) | PASS (487개 OK, 합산) |
| `git diff --check` | PASS |

---

## 범위 준수 확인

- scope-in: watcher_core.py, supervisor.py, runtime_policy.json, 새 테스트, work note ✓
- scope-out: verify_fsm.py, verify_accept_deadline_sec, 프로덕트 소스, commit/push/PR ✓

## 이번 fix가 다루는 것 vs 남은 것

| 구분 | 상태 |
|---|---|
| 정상 처리 시간을 stall로 오판하는 false positive 방지 (45s → 300s) | **이번 fix** ✓ |
| lane kill 시 `finish_stream()` 호출 미보장 → TASK_DONE 손실 | **미해결** (별도 슬라이스) |

---

## 다음 슬라이스 방향

SIGTERM 핸들링으로 `claude-print-jsonl-pipe` 프로세스가 인터럽트될 때 `finish_stream()`을 보장하는 슬라이스가 필요하지만, `verify_done_deadline_sec=300s`로 인해 lane kill이 정상 처리 중 발생하는 false positive가 먼저 제거됐음. 다음 우선순위 결정은 운영 재관찰 결과에 따름.
