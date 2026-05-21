# verify: 2026-05-21 Claude print pipe opt-in subcommand

## 대상 work

`work/5/21/2026-05-21-claude-print-pipe-opt-in-subcommand.md`

## 이전 verify

`verify/5/21/2026-05-21-claude-print-pipe-prompt-source-contract.md`

## 검증 결과

`VERIFY_DONE`.

최신 `/work`의 핵심 주장인 explicit local opt-in `claude-print-jsonl-pipe`
subcommand 추가, `--project-root`/`--run-id` 기반 wrapper event 경로 산출,
prompt-source helper 재사용, prompt-source 거부 시 `2` 반환 및 subprocess 미호출,
stderr passthrough, 기존 `_lane_wrapper()`/supervisor 기본 Claude pane text mode 미변경은
현재 코드와 재실행 검증 기준으로 사실입니다.

## 사용 skill

- `round-handoff`: 최신 구현 closeout을 코드와 targeted 검증으로 재확인하고
  `/verify` 기록을 남기기 위해 사용했습니다.
- `next-slice-triage`: 검증 truth가 현재화된 뒤 advisory/operator가 아닌 다음
  bounded local slice를 하나로 좁히기 위해 사용했습니다.

## 변경 파일

변경 파일 - 없음. 이 라운드는 검증 및 control 작성 라운드이며 구현 파일은 수정하지
않았습니다.

## 확인한 대상

- `AGENTS.md`
- `.pipeline/harness/verify.md`
- `.pipeline/harness/council.md`
- `work/5/21/2026-05-21-claude-print-pipe-opt-in-subcommand.md`
- `verify/5/21/2026-05-21-claude-print-pipe-prompt-source-contract.md`
- `pipeline_runtime/cli.py`
- `tests/test_pipeline_runtime_cli.py`

## 재실행 검증

- `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py`
  - 결과: PASS, 출력 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_subcommand_calls_prompt_file_helper tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_subcommand_rejects_prompt_source_without_subprocess tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_from_prompt_file_accepts_local_utf8_file tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_prompt_source_rejects_invalid_inputs_without_subprocess tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_sends_prompt_and_feeds_stdout tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_returns_stderr_and_nonzero_exit tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_initializes_all_lanes_in_text_mode`
  - 결과: PASS. `Ran 7 tests in 0.027s`, `OK`.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_lane_vendor_command_keeps_claude_default_in_pane_text_mode`
  - 결과: PASS. `Ran 1 test in 0.004s`, `OK`.
- `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py work/5/21/2026-05-21-claude-print-pipe-opt-in-subcommand.md`
  - 결과: PASS, 출력 없음.

## 코드 확인

- `pipeline_runtime/cli.py`
  - `_claude_print_jsonl_pipe_command()`는 `_project_root(args.project_root)`를 사용해
    project root를 해석합니다.
  - wrapper event directory는
    `<project_root>/.pipeline/runs/<run-id>/wrapper-events`로 생성됩니다.
  - `task_hint_dir`는 값이 있을 때 `Path(...).resolve()`로 전달되고, 없으면
    `None`입니다.
  - subcommand는 `_run_claude_print_jsonl_pipe_from_prompt_file()`에
    `allowed_root=project_root`, `cwd=project_root`, `claude_bin=args.claude_bin`을
    넘깁니다.
  - `ClaudePrintPromptSourceError`는 stderr에
    `claude_print_jsonl_prompt_source_error: <code>: <path>` 형태로 기록되고
    return code `2`로 끝납니다.
  - `_lane_wrapper()`는 여전히 `_WrapperEmitter(..., jsonl_mode=False)`로 초기화되며
    opt-in subcommand를 호출하지 않습니다.
- `tests/test_pipeline_runtime_cli.py`
  - subcommand helper 호출 인자, wrapper dir 생성, stderr passthrough를 확인합니다.
  - prompt-source rejection path에서 `_run_claude_print_jsonl_pipe()`와
    `subprocess.Popen`이 호출되지 않는지 확인합니다.
  - 기존 prompt-source helper, fake subprocess, lane text-mode tests가 계속 통과합니다.

## 실행하지 않은 검증

- live `claude` 실행, tmux/session access, controller/browser server, Playwright,
  full smoke, long soak는 실행하지 않았습니다.
- broad unittest 전체 묶음은 실행하지 않았습니다. 이번 변경은
  `pipeline_runtime/cli.py` subcommand와 해당 targeted tests에 한정됩니다.
- commit, push, branch/PR publication, PR creation, merge, release는 실행하지
  않았습니다.

## 런타임 표면

Prompt에 포함된 `RUNTIME_STATUS_AT_DISPATCH`를 권위 있는 dispatcher surface로
사용했습니다.

- `runtime_state: RUNNING`
- `automation_health: recovering`
- `automation_next_action: retrying`
- `active_control: .pipeline/implement_handoff.md#2084 implement`
- `turn_state: IDLE`
- `active_round: VERIFY_PENDING`

lane-local `status --json`, `doctor --json`, `tmux` 확인은 실행하지 않았고, 그
종류의 lane-local access mismatch를 operator boundary 근거로 사용하지 않았습니다.

## 판정

- 최신 `/work`의 구현 주장은 검증 완료입니다.
- 이번 변경은 explicit opt-in CLI route까지만 열었고 shipped/default Claude lane
  behavior는 바꾸지 않았습니다.
- 현재 route test는 helper 호출을 mock하고 helper/fake subprocess tests는 별도로
  존재합니다. 다음 같은-family risk reduction은 live/tmux 없이 subcommand에서 실제
  prompt file, fake subprocess, wrapper event까지 이어지는 local fake e2e replay를
  추가하는 것입니다.

## 남은 리스크

- `claude-print-jsonl-pipe`는 local opt-in subcommand이며 supervisor default lane에
  연결되지 않았습니다.
- 아직 `main(["claude-print-jsonl-pipe", ...])`가 실제 prompt file과 fake
  `subprocess.Popen`을 통해 wrapper event까지 생성하는 end-to-end unit replay는 없습니다.
- live Claude/tmux 검증은 계속 보류이며, 다음 slice도 fake subprocess/local file
  검증에 머물러야 합니다.
- 현재 worktree에는 이번 Claude print-pipe 계열 외 기존 dirty/untracked 항목이
  남아 있습니다.
- publication은 계속 held 상태입니다.

## 다음 컨트롤 판단

COUNCIL_DECISION: implement
REASON_CODE: claude_print_pipe_subcommand_fake_e2e_replay
OWNER_ROLE: implement
NEXT_CONTROL_FILE: .pipeline/implement_handoff.md
NEXT_CONTROL_SEQ: 2085

EVIDENCE:
- `work/5/21/2026-05-21-claude-print-pipe-opt-in-subcommand.md`
- `verify/5/21/2026-05-21-claude-print-pipe-opt-in-subcommand.md`
- `pipeline_runtime/cli.py`
- `tests/test_pipeline_runtime_cli.py`
- `RUNTIME_STATUS_AT_DISPATCH`: `RUNNING`, `automation_health=recovering`,
  `automation_next_action=retrying`, `active_control=.pipeline/implement_handoff.md#2084 implement`

REJECTED:
- `.pipeline/operator_request.md`: destructive write, credential/auth,
  approval-record repair, truth-sync blocker, merge, release, external
  publication, or immediate safety boundary가 없습니다.
- `.pipeline/advisory_request.md`: 같은 Claude print-pipe family에서 helper-mock
  route test와 fake subprocess helper test 사이의 통합 replay가 명확한 다음
  current-risk reduction이므로 advisory tie-break가 필요하지 않습니다.
- default lane wiring/full smoke/release readiness: 현재 evidence는 local fake e2e
  replay까지만 정당화하며 default lane 전환, full-smoke pass, release-ready,
  publication-ready 주장을 지원하지 않습니다.
- commit/push/PR handoff: implement prompt가 commit, push, branch/PR publication,
  PR creation, merge, release를 금지합니다.
