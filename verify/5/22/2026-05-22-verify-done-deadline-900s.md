# verify: 2026-05-22 verify done deadline 900s (2150)

## 대상 work
`work/5/22/2026-05-22-verify-done-deadline-900s.md`

## 검증 결과: READY

---

## 코드 확인

| 항목 | 위치 | 확인 |
|---|---|---|
| `DEFAULT_VERIFY_DONE_DEADLINE_SEC = 900.0` | `watcher_core.py` | ✓ |
| `"verify_done_deadline_sec": 900` | `.pipeline/config/runtime_policy.json` | ✓ |
| `test_default_verify_done_deadline_is_900_seconds` | `tests/test_watcher_core.py` | ✓ |

## 회귀 검증

| 검사 | 결과 |
|---|---|
| `python3 -m py_compile watcher_core.py` | PASS |
| policy assertion `== 900` | PASS |
| default assertion `== 900.0` | PASS |
| `test_default_verify_done_deadline_is_900_seconds` | PASS |
| 전체 548개 suite (cli + supervisor + watcher_core) | **PASS (0 FAIL, 0 ERROR)** |
| `git diff --check` | PASS |

---

## 변경 이력

| CONTROL_SEQ | 값 | 근거 |
|---|---|---|
| 2129 | 45s → 300s | live 관찰: Codex 40s, Claude 48s stall |
| **2150** | **300s → 900s** | live 관찰: Claude TASK_DONE 7분 3초, 300s 초과 |

---

## 다음 단계

trigger-9를 fresh work로 생성 후 파이프라인 재시작:
- 900s deadline 내 Claude verify 완료 예상
- **중요:** trigger-9 verify note는 live TASK_DONE 관찰 후에만 작성
