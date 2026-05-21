# 2026-05-21 live Claude stream-json validation

## 변경 파일
- `work/5/21/2026-05-21-live-claude-stream-json-validation.md` 신규 작성
- 코드, 설정, 프로필 파일은 수정하지 않았습니다.

## 사용 skill
- `security-gate`: live Claude 실행, 임시 tmux PTY, runtime 이벤트 관찰이 승인 경계와 publication 경계를 넘지 않는지 확인하기 위해 사용했습니다.
- `work-log-closeout`: CONTROL_SEQ 2108 관찰 결과와 다음 슬라이스 방향을 `/work`에 남기기 위해 사용했습니다.

## 변경 이유
- `.pipeline/operator_request.md#2078`의 `AUTHORIZE_LIVE_CLAUDE_STREAM_JSON_VALIDATION` 결정에 따라 Claude Code 2.1.146에서 `--output-format stream-json`이 실제 lane wrapper 전제와 맞는지 확인했습니다.
- 이전 구현은 Claude lane vendor command에 `--output-format stream-json`을 붙이고, `pipeline_runtime.cli`의 `_WrapperEmitter`가 Claude lane을 `jsonl_mode=True`로 처리하는 구조였습니다.
- `claude --help`는 `--output-format`이 `--print` 전용이라고 표시하므로, `--print` 기준선과 tmux PTY 실제 동작을 분리해 확인했습니다.

## 핵심 변경
- Step 1 기준선: 요청된 원 명령은 실패했습니다.
  - 실행: `timeout 90 bash -lc 'echo "respond with exactly: OK" | claude --print --output-format stream-json --dangerously-skip-permissions 2>&1 | head -20'`
  - 결과: `Error: When using --print, --output-format=stream-json requires --verbose`
- Step 1 보정 기준선: Claude 2.1.146 요구사항에 맞게 `--verbose`를 추가하면 JSONL이 출력됩니다.
  - 실행: `timeout 120 bash -lc 'echo "respond with exactly: OK" | claude --print --verbose --output-format stream-json --dangerously-skip-permissions 2>&1 | head -20'`
  - 관찰 샘플:
    ```jsonl
    {"type":"system","subtype":"hook_started",...}
    {"type":"system","subtype":"hook_response",...}
    {"type":"system","subtype":"init",...}
    {"type":"assistant","message":{"content":[{"type":"text","text":"OK"}],...},...}
    {"type":"rate_limit_event",...}
    {"type":"result","subtype":"success","is_error":false,"result":"OK",...}
    ```
- Step 2 현재 pipeline 이벤트: `.pipeline/current_run.json`의 run은 `20260521T110947Z-p327825`이고 `events.jsonl`은 13줄이었습니다. 최근 이벤트에서 Claude lane의 `TASK_ACCEPTED` 또는 `pane_text_fallback_used`는 관찰되지 않았습니다.
- Step 2 제약: 현재 `.pipeline/config/agent_profile.json`은 `selected_agents: ["Codex"]`이고 Claude lane이 활성화되어 있지 않습니다. STOP_RULE에 따라 검증을 위해 profile을 수정하지 않았습니다.
- Step 2 tmux PTY 직접 검증: 임시 tmux 세션에서 `exec claude --output-format stream-json --dangerously-skip-permissions`를 실행한 뒤 pane을 캡처하고 세션을 종료했습니다.
  - 관찰 샘플:
    ```text
     ▐▛███▜▌   Claude Code v2.1.146
    ▝▜█████▛▘  Sonnet 4.6 with high effort · Claude Pro
      ▘▘ ▝▝    ~/code/projectH

    ❯
      ⏵⏵ bypass permissions on (shift+tab to cycle) · ← for agents
    ```
- 판정: 케이스 B입니다. tmux PTY에서 `--output-format stream-json`은 JSONL을 내보내지 않고 Claude Code TUI를 표시합니다.

## 검증
- 확인: `claude --version`
  - 결과: `2.1.146 (Claude Code)`
- 확인: `claude --help | rg -n "output-format|print|stream-json"`
  - 결과: `--output-format <format>`은 `only works with --print`로 표시됩니다.
- 실패 확인: `echo "respond with exactly: OK" | claude --print --output-format stream-json --dangerously-skip-permissions`
  - 결과: `--output-format=stream-json requires --verbose`
- 실패 확인: `echo "OK" | claude --print --output-format stream-json --dangerously-skip-permissions 2>&1 | head -10`
  - 결과: `--output-format=stream-json requires --verbose`
- 통과 확인: `echo "respond with exactly: OK" | claude --print --verbose --output-format stream-json --dangerously-skip-permissions`
  - 결과: `system`, `assistant`, `rate_limit_event`, `result` JSONL 이벤트가 출력되고 `result: "OK"`로 종료했습니다.
- 확인: `.pipeline/current_run.json`과 해당 `events.jsonl` 최근 이벤트 검사
  - 결과: Claude lane의 `TASK_ACCEPTED` 또는 `pane_text_fallback_used` 없음
- 확인: 임시 tmux PTY에서 `claude --output-format stream-json --dangerously-skip-permissions`
  - 결과: JSONL이 아니라 TUI 출력
- 통과: `git diff --check -- work/5/21/`

## 남은 리스크
- 현재 Claude lane이 profile에서 비활성이라 live pipeline 안에서 `TASK_ACCEPTED source=wrapper` 또는 `pane_text_fallback_used lane=Claude`까지는 관찰하지 못했습니다.
- 다만 같은 PTY 조건에서 Claude Code가 TUI를 출력함을 확인했으므로, 현재 lane wrapper의 `jsonl_mode=True` 전제는 live 동작과 맞지 않습니다.
- 다음 슬라이스 방향은 `claude --print --verbose --output-format stream-json`을 stdin 파이프로 실행하는 별도 wrapper 구조입니다. tmux pane은 사람 모니터용으로 분리하거나, wrapper가 pipe 기반 실행 결과를 pane에 미러링하는 구조가 필요합니다.
- 이번 라운드에서는 수정 구현, profile 변경, commit, push, PR, merge, publish를 실행하지 않았습니다.
