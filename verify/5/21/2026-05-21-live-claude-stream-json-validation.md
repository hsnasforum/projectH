# verify: 2026-05-21 live Claude stream-json validation (operator_request#2078)

## 대상 work
`work/5/21/2026-05-21-live-claude-stream-json-validation.md`

## 검증 결과: 케이스 B 확정 — 현재 구현 교정 필요

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `claude --version` | 2.1.146 |
| `--print --output-format stream-json` | 실패 (--verbose 없이) |
| `--print --verbose --output-format stream-json` | JSONL 출력 ✓ |
| tmux PTY + `--output-format stream-json` (lane 실제 구현) | TUI 출력 → JSONL 아님 |
| `git diff --check -- work/5/21/` | PASS |

## 핵심 판정

**tmux PTY 인터랙티브 세션에서 `--output-format stream-json`은 동작하지 않는다.**

Claude Code v2.1.146에서 `--output-format stream-json`은 `--print` 모드
전용이며, PTY 세션에서는 일반 TUI를 출력한다.

현재 구현:
- `_lane_vendor_command("Claude")` → `exec claude --output-format stream-json`
- `_WrapperEmitter(jsonl_mode=True)` → 첫 TUI 출력에서 JSON 파싱 실패
- → `jsonl_mode=False` fallback → pane text로 전환
- → pane_text_fallback_used 이벤트 발생 (Claude lane도 fallback에 의존)

## 현재 실제 동작

stream-json 구현 이전과 동작 차이 없음. `jsonl_mode=False` fallback이
즉시 트리거되어 기존 pane text 경로로 처리됨. 기능 회귀는 없지만
stream-json의 구조적 이점도 없음.

## 다음 슬라이스 방향

**올바른 구현: stdin 파이프 기반 --print 모드 wrapper**

```
현재 (잘못됨):
  tmux pane → exec claude --output-format stream-json
  → PTY TUI 출력 → json 파싱 실패 → fallback

올바른 구조:
  프롬프트를 stdin pipe로 전달
  claude --print --verbose --output-format stream-json < prompt.txt
  → JSONL stdout → _WrapperEmitter._feed_jsonl() 정상 파싱
  → TASK_ACCEPTED source=wrapper
```

단기 대안 (즉시 적용 가능):
  `_lane_vendor_command("Claude")`에서 `--output-format stream-json` 제거.
  jsonl_mode 코드는 보존 (아키텍처 준비).
  Claude lane은 기존 pane text fallback 경로 유지.
  pane_text_fallback_used 이벤트가 Claude에도 기록되어 관찰 가능.

## operator_request#2078 처리 결과

AUTHORIZE_LIVE_CLAUDE_STREAM_JSON_VALIDATION 결정에 따른 검증 완료.
결과가 케이스 B이므로 현재 stream-json 구현은 무효이며 교정 필요.
HOLD_LIVE_VALIDATION_LOCAL_ONLY 수준으로 돌아가는 것이 안전.
