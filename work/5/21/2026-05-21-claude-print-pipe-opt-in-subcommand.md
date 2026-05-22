# 2026-05-21 Claude print pipe opt-in subcommand

## 변경 파일
- `pipeline_runtime/cli.py`
- `tests/test_pipeline_runtime_cli.py`
- `work/5/21/2026-05-21-claude-print-pipe-opt-in-subcommand.md`

## 사용 skill
- `security-gate`: explicit CLI/subprocess 경계가 live/default lane으로 번지지 않고 local-only opt-in에 머무르는지 확인하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 미실행 범위, 남은 리스크를 `/work` 형식으로 기록하기 위해 사용했습니다.

## 변경 이유
- Claude print JSONL pipe scaffold와 prompt-source contract가 준비된 뒤, 기본 lane behavior를 바꾸지 않는 명시적 opt-in CLI 경로가 필요했습니다.
- 이번 변경은 `claude --print --verbose --output-format stream-json` pipe helper를 직접 default lane에 연결하지 않고, 로컬 subcommand를 통해서만 호출되도록 제한합니다.

## 핵심 변경
- `pipeline_runtime/cli.py`에 `claude-print-jsonl-pipe` subcommand를 추가했습니다.
- subcommand는 `--project-root`, `--run-id`, `--prompt-file`, `--task-hint-dir`, `--claude-bin`을 받아 기존 prompt-file helper로만 연결합니다.
- wrapper event 경로는 `<project_root>/.pipeline/runs/<run-id>/wrapper-events`로 고정하고, prompt file은 기존 `allowed_root=project_root` 계약을 재사용합니다.
- prompt-source 거부는 stderr에 구조화된 code/path를 남기고 return code `2`로 끝나며 subprocess를 호출하지 않습니다.
- `_lane_wrapper()`와 supervisor 기본 command/profile, tmux 경로는 변경하지 않았습니다.
- 새 테스트는 opt-in subcommand의 helper 호출 인자, wrapper dir 생성, stderr passthrough, prompt-source 거부 시 subprocess 미호출을 확인합니다.

## 검증
- `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py`
  - 결과: PASS, 출력 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_subcommand_calls_prompt_file_helper tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_subcommand_rejects_prompt_source_without_subprocess tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_from_prompt_file_accepts_local_utf8_file tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_prompt_source_rejects_invalid_inputs_without_subprocess tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_sends_prompt_and_feeds_stdout tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_returns_stderr_and_nonzero_exit tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_initializes_all_lanes_in_text_mode`
  - 결과: PASS. `Ran 7 tests in 0.038s`, `OK`.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_lane_vendor_command_keeps_claude_default_in_pane_text_mode`
  - 결과: PASS. `Ran 1 test in 0.006s`, `OK`.
- `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py work/5/21/`
  - 결과: PASS, 출력 없음.

## 남은 리스크
- live `claude`, tmux/session access, controller/browser server, Playwright, full smoke, long soak는 실행하지 않았습니다.
- 이번 subcommand는 explicit opt-in 경로이며, shipped/default Claude lane은 여전히 pane text mode입니다.
- broad unittest 전체 묶음은 실행하지 않았습니다. 변경 범위는 `pipeline_runtime/cli.py`와 해당 targeted tests에 한정됩니다.
- commit, push, branch/PR publication, merge, release, publication 작업은 수행하지 않았습니다.
