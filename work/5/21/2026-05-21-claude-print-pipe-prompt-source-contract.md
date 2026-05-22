# 2026-05-21 Claude print pipe prompt source contract

## 변경 파일
- `pipeline_runtime/cli.py`
- `tests/test_pipeline_runtime_cli.py`
- `work/5/21/2026-05-21-claude-print-pipe-prompt-source-contract.md`

## 사용 skill
- `security-gate`
- `work-log-closeout`

## 변경 이유
- `claude --print --verbose --output-format stream-json` 비PTY scaffold가 아직 비활성 경로이더라도, 이후 명시적으로 연결될 때 prompt 입력이 임의 문자열이나 루트 밖 파일에서 들어오지 않도록 local-only prompt-source 계약을 먼저 고정해야 했습니다.
- 기존 live Claude, tmux pane-text lane, 기본 Claude profile 동작은 변경하지 않는 범위에서 prompt 파일 로딩과 거부 조건만 추가했습니다.

## 핵심 변경
- `pipeline_runtime/cli.py`에 `ClaudePrintPromptSourceError`와 prompt 경로 해석/로딩 헬퍼를 추가했습니다.
- prompt 파일은 명시된 `allowed_root` 아래의 UTF-8 로컬 파일만 허용합니다.
- 루트 밖으로 해석되는 경로, 누락 파일, 디렉터리, 공백-only prompt는 구조화된 error code로 거부합니다.
- 허용된 prompt text만 `_run_claude_print_jsonl_pipe()`로 전달하고, 기본 `cwd`는 해석된 local root로 고정합니다.
- 거부 입력에서는 `_run_claude_print_jsonl_pipe()`와 `subprocess.Popen`이 호출되지 않도록 테스트로 고정했습니다.
- 기존 lane wrapper는 계속 pane-text 모드로 초기화되며 live `claude`, tmux, profile, launcher wiring은 건드리지 않았습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py`
- `python3 -m unittest -v tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_from_prompt_file_accepts_local_utf8_file tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_prompt_source_rejects_invalid_inputs_without_subprocess tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_sends_prompt_and_feeds_stdout tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_returns_stderr_and_nonzero_exit tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_initializes_all_lanes_in_text_mode`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_lane_vendor_command_keeps_claude_default_in_pane_text_mode`
- `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py work/5/21/2026-05-21-claude-print-pipe-prompt-source-contract.md`

## 남은 리스크
- 이 라운드는 inactive scaffold의 prompt-source 계약만 다뤘으며 live Claude 실행, tmux lane, Playwright/full smoke는 실행하지 않았습니다.
- commit, push, branch/PR publish, merge, release 작업은 수행하지 않았습니다.
