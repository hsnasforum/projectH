# 2026-05-21 Claude print pipe subcommand fake e2e replay

## 변경 파일
- `tests/test_pipeline_runtime_cli.py`
- `work/5/21/2026-05-21-claude-print-pipe-subcommand-fake-e2e-replay.md`

## 사용 skill
- `security-gate`: subprocess 실행 경계가 live `claude`나 default lane으로 확장되지 않고 fake-local replay에 머무르는지 확인하기 위해 사용했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 미실행 범위, 남은 리스크를 `/work` 형식으로 기록하기 위해 사용했습니다.

## 변경 이유
- 기존 `claude-print-jsonl-pipe` subcommand 테스트는 helper 호출을 mock했고, fake subprocess helper 테스트는 subcommand를 통하지 않았습니다.
- 명시 opt-in CLI 경로가 실제 prompt file 로딩부터 fake subprocess stdout, wrapper event 기록까지 이어지는지 local-only replay로 잠글 필요가 있었습니다.

## 핵심 변경
- `tests/test_pipeline_runtime_cli.py`에 `test_claude_print_jsonl_pipe_subcommand_fake_e2e_emits_wrapper_events`를 추가했습니다.
- 테스트는 임시 project root 안에 UTF-8 prompt file과 Claude task hint를 쓰고 `runtime_cli.main(["claude-print-jsonl-pipe", ...])`를 호출합니다.
- `_run_claude_print_jsonl_pipe_from_prompt_file()`와 `_run_claude_print_jsonl_pipe()`는 mock하지 않고, `runtime_cli.subprocess.Popen`만 fake process로 대체합니다.
- fake process가 prompt bytes를 stdin으로 받는지, command shape와 `cwd`가 기대와 맞는지 확인합니다.
- run-specific wrapper event path의 `claude.jsonl`에 `DISPATCH_SEEN`, `TASK_ACCEPTED`, `TASK_DONE`, `READY`가 기록되고 task hint identity가 보존되는지 확인합니다.
- replay 통과로 생산 코드 수정은 필요하지 않았습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py`
  - 결과: PASS, 출력 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_subcommand_fake_e2e_emits_wrapper_events`
  - 결과: PASS. `Ran 1 test in 0.013s`, `OK`.
- `python3 -m unittest -v tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_subcommand_fake_e2e_emits_wrapper_events tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_subcommand_calls_prompt_file_helper tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_subcommand_rejects_prompt_source_without_subprocess tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_from_prompt_file_accepts_local_utf8_file tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_prompt_source_rejects_invalid_inputs_without_subprocess tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_sends_prompt_and_feeds_stdout tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_returns_stderr_and_nonzero_exit tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_initializes_all_lanes_in_text_mode`
  - 결과: PASS. `Ran 8 tests in 0.049s`, `OK`.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_lane_vendor_command_keeps_claude_default_in_pane_text_mode`
  - 결과: PASS. `Ran 1 test in 0.004s`, `OK`.
- `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py work/5/21/`
  - 결과: PASS, 출력 없음.

## 남은 리스크
- live `claude`, tmux/session access, controller/browser server, Playwright, full smoke, long soak는 실행하지 않았습니다.
- 이번 replay는 fake subprocess 기반 local unit replay이며, shipped/default Claude lane은 여전히 pane text mode입니다.
- broad unittest 전체 묶음은 실행하지 않았습니다. 변경 범위는 `tests/test_pipeline_runtime_cli.py`의 targeted replay에 한정됩니다.
- `pipeline_runtime/cli.py`에는 이전 Claude print-pipe 라운드의 dirty 변경이 남아 있지만, 이번 라운드에서는 생산 코드를 추가 수정하지 않았습니다.
- commit, push, branch/PR publication, merge, release, publication 작업은 수행하지 않았습니다.
