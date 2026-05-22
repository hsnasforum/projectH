# verify: 2026-05-21 Claude print-jsonl lane integration (2112)

## 대상 work
`work/5/21/2026-05-21-claude-print-jsonl-lane-integration.md`

## 검증 결과: READY (unit 범위)

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `py_compile` supervisor / watcher_dispatch | PASS |
| `unittest` supervisor 221개 + watcher 16개 | PASS |
| lane routing assertion | Claude→print-pipe, Codex→lane-wrapper ✓ |
| `git diff --check` | PASS |

## 코드 확인

| 항목 | 위치 | 확인 |
|---|---|---|
| `_claude_print_lane_shell_command()` 신규 | supervisor.py:2877 | ✓ |
| `_lane_shell_command("Claude")` → print watchdog | supervisor.py | ✓ |
| `_lane_shell_command("Codex")` → lane-wrapper 유지 | supervisor.py | ✓ |
| `_write_claude_pending_prompt()` temp→rename atomic | watcher_dispatch.py:275–283 | ✓ |
| non-Claude lane → send-keys 경로 유지 | watcher_dispatch.py | ✓ |

## 아직 미검증

- live tmux 환경에서 watchdog 루프 실제 동작
- claude-print-jsonl-pipe 호출 → JSONL 수신 → TASK_ACCEPTED 발생
- profile에서 Claude가 active lane일 때 end-to-end

## 다음 슬라이스

live 환경에서 Claude lane이 active일 때
events.jsonl에서 TASK_ACCEPTED source=wrapper 확인.
pane_text_fallback_used 이벤트가 Claude에서 발생하지 않으면 성공.
