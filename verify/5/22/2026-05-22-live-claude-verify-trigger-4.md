# verify: 2026-05-22 live Claude verify trigger 4 (2130)

## 대상 work
`work/5/22/2026-05-22-live-claude-verify-trigger-4.md`

## 검증 결과: READY (implement 완료, 관찰 대기 중)

---

## 파일 확인

| 확인 항목 | 결과 |
|---|---|
| `work/5/22/2026-05-22-live-claude-verify-trigger-4.md` 존재 | ✓ |
| 소스 코드 변경 없음 | ✓ (git status: M 파일은 CONTROL_SEQ 2129 변경, 이 slice와 무관) |
| `verify/`, `.pipeline/` 변경 없음 | ✓ |
| `git diff --check` | PASS |

---

## 현재 working tree 상태 요약

CONTROL_SEQ 2129 변경(미커밋)이 working tree에 누적되어 있음:

| 파일 | 상태 | 내용 |
|---|---|---|
| `watcher_core.py` | M (미커밋) | `verify_done_deadline_sec` 기본값 45→300, `--verify-done-deadline` CLI 플래그 |
| `pipeline_runtime/supervisor.py` | M (미커밋) | runtime_policy.json에서 deadline 읽어 watcher에 전달 |
| `.pipeline/config/runtime_policy.json` | M (미커밋) | `"verify_done_deadline_sec": 300` |
| `tests/test_watcher_core.py` | M (미커밋) | 새 회귀 테스트 |
| `tests/test_pipeline_runtime_supervisor.py` | M (미커밋) | 새 회귀 테스트 |

---

## 다음 관찰 조건

파이프라인을 현재 working tree 기준으로 재시작하면:
- trigger-4 (`work/5/22/2026-05-22-live-claude-verify-trigger-4.md`)가 Claude lane에 전달됨
- `verify_done_deadline_sec=300s` 적용 상태
- **관찰 목표**: `TASK_DONE source=wrapper lane=Claude` 수신 여부

성공 시: A3 Step 6 (WatcherCore turn state machine 설계) 진입 조건 충족.
실패 시: SIGTERM 핸들링 슬라이스(`finish_stream()` 보장) 선행 필요.
