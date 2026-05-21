# verify: 2026-05-21 Claude stream-json flag revert (2109)

## 대상 work
`work/5/21/2026-05-21-claude-stream-json-flag-revert.md`

## 검증 결과: READY

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `py_compile` supervisor / cli | PASS |
| `unittest` supervisor + cli 264개 | PASS (2.417s) |
| Claude command assertion | `--output-format` not in command ✓ |
| `git diff --check` | PASS |

## 코드 확인

| 항목 | 위치 | 확인 |
|---|---|---|
| Claude lane command: `--output-format` 제거 | supervisor.py | ✓ |
| `_WrapperEmitter(jsonl_mode=False)` 고정 | cli.py:928 | ✓ |
| `_feed_jsonl` / `_on_claude_activity` 코드 보존 | cli.py:992 | ✓ |

## stream-json 시도 전/후 비교

| 항목 | Step 3 구현 후 | 이번 교정 후 |
|---|---|---|
| Claude lane command | `--output-format stream-json` 포함 | 제거 |
| WrapperEmitter 초기화 | `jsonl_mode=True` | `jsonl_mode=False` |
| 실제 동작 | TUI → JSON 실패 → fallback | pane text (직접) |
| 결과 | 동일 (fallback 즉시 트리거) | 동일 (명시적) |

기능 회귀 없음. 코드 의도가 명확해짐.

## 남은 미완 항목

| 항목 | 상태 |
|---|---|
| `--print` stdin 파이프 wrapper 구조 | 설계 필요 (중장기) |
| Claude active lane live 검증 | profile 변경 필요 |
| jsonl_mode 코드 | 보존됨 — 향후 재활성화 대기 중 |
