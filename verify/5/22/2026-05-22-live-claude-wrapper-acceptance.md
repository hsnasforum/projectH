# verify: 2026-05-22 live Claude wrapper acceptance

## 검증 결과: READY (목표 조건 충족)

## live 관찰 이벤트

run_id: 20260522T040034Z-p31147

| 이벤트 | source | lane | 확인 |
|---|---|---|---|
| DISPATCH_SEEN | wrapper | Claude | ✓ |
| TASK_ACCEPTED | wrapper | Claude | ✓ |

job_id: 20260522-2026-05-22-live-claude-verify-tr-5425a718

## 수정 내용

| 문제 | 수정 |
|---|---|
| Claude verify dispatch가 send-keys로 빠지던 경로 | claude.prompt.pending 파일 쓰기로 교정 |
| claude-print-jsonl-pipe stdout 실시간 읽기 미흡 | assistant 이벤트만으로 TASK_ACCEPTED 발생하도록 수정 |

## 테스트

| 검사 | 결과 |
|---|---|
| `py_compile` cli.py / watcher_dispatch.py | PASS |
| test_pipeline_runtime_cli + test_verify_fsm + test_watcher_core 331개 | PASS |
| `git diff --check` | PASS |

## 남은 항목

- pane_text_fallback_used lane=Claude 노이즈 (dispatch 전 supervisor 감지)
- TASK_DONE end-to-end 확인 미완
- cli.py 변경 42줄 커밋 대기 중

## 의의

Claude watchdog lane이 실제 운영 환경에서 wrapper event 경로(source=wrapper)로
TASK_ACCEPTED를 수신하는 것이 처음으로 확인됨.
pane text send-keys가 아닌 pending 파일 → claude-print-jsonl-pipe 경로 동작 검증.
