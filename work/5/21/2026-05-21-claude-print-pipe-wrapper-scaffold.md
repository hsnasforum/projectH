# 2026-05-21 Claude print pipe wrapper scaffold

## 변경 파일
- `pipeline_runtime/cli.py`
- `tests/test_pipeline_runtime_cli.py`
- `work/5/21/2026-05-21-claude-print-pipe-wrapper-scaffold.md`

## 사용 skill
- `security-gate`: subprocess 기반 Claude print JSONL scaffold가 live 실행, tmux,
  publication, approval 경계를 넓히지 않는지 확인하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 실행하지 않은 검증, 남은 리스크를
  한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- live 검증에서 Case B가 확인됐습니다. tmux PTY에서
  `--output-format stream-json`은 JSONL이 아니라 Claude TUI를 출력합니다.
- 단기 교정으로 Claude lane 기본 경로는 pane text mode에 남아 있습니다.
- 장기 전환 후보인 `claude --print --verbose --output-format stream-json`
  stdin pipe 구조를 live 실행 없이 local fake subprocess 테스트로 먼저 고정하기
  위해 이번 slice를 수행했습니다.

## 핵심 변경
- `pipeline_runtime/cli.py`에 `_CLAUDE_PRINT_JSONL_ARGS`,
  `_decode_subprocess_stream()`, `_run_claude_print_jsonl_pipe()`를 추가했습니다.
- 새 helper는 직접 호출될 때만 `claude --print --verbose --output-format stream-json`
  command shape를 만들고, prompt를 subprocess stdin으로 보냅니다.
- stdout JSONL은 기존 `_WrapperEmitter(jsonl_mode=True)` 경로로 전달합니다.
- stderr는 별도 문자열로 반환해 stdout JSONL 파싱 경로와 섞지 않습니다.
- `_lane_wrapper()` 기본 흐름, `_lane_vendor_command()`, active profile, tmux,
  controller/browser 경로는 변경하지 않았습니다.
- `tests/test_pipeline_runtime_cli.py`에 fake `subprocess.Popen` 기반 테스트 2개를
  추가해 prompt stdin 전달, stdout JSONL wrapper event 생성, stderr/nonzero exit
  반환을 확인했습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py`
- 통과: `python3 -m unittest -v tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_sends_prompt_and_feeds_stdout tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_returns_stderr_and_nonzero_exit tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_text_event_emits_task_accepted tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_tool_use_event_emits_task_accepted tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_result_event_emits_task_done tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_stream_finish_emits_task_done tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_invalid_output_falls_back_to_text_parsing tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_initializes_all_lanes_in_text_mode`
  - 결과: `Ran 8 tests in 0.020s`, `OK`
- 통과: `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_lane_vendor_command_keeps_claude_default_in_pane_text_mode`
  - 결과: `Ran 1 test in 0.004s`, `OK`
- 통과: `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py`
- 통과: `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py work/5/21/`

## 남은 리스크
- 이번 helper는 inactive/non-default scaffold입니다. `_lane_wrapper()` 기본 동작에
  연결하지 않았고 live Claude validation pass를 주장하지 않습니다.
- live `claude`, tmux/session access, controller/browser server, Playwright,
  full smoke, long soak는 실행하지 않았습니다.
- commit, push, branch/PR publication, merge, release, publication 작업은
  실행하지 않았습니다.
- 현재 worktree에는 이번 slice 밖의 기존 dirty 항목이 남아 있습니다. 이번 라운드는
  `pipeline_runtime/cli.py`, `tests/test_pipeline_runtime_cli.py`, 이 `/work` 기록만
  변경했습니다.
