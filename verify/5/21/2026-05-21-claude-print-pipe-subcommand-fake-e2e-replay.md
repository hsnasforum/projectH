# verify: 2026-05-21 Claude print pipe subcommand fake e2e replay

## 대상 work

`work/5/21/2026-05-21-claude-print-pipe-subcommand-fake-e2e-replay.md`

## 이전 verify

`verify/5/21/2026-05-21-claude-print-pipe-opt-in-subcommand.md`

## 검증 결과

`VERIFY_DONE`.

최신 `/work`의 핵심 주장인 `claude-print-jsonl-pipe` subcommand fake e2e replay
추가, 실제 local prompt file 로딩, fake `subprocess.Popen`만 대체한 subprocess stdin
검증, command shape 및 `cwd` 검증, run-specific wrapper event path의 `claude.jsonl`
기록 검증, task hint identity 보존 검증, 생산 코드 미수정은 현재 코드와 재실행 검증
기준으로 사실입니다.

## 사용 skill

- `round-handoff`: 최신 구현 closeout을 코드와 targeted 검증으로 재확인하고
  `/verify` 기록을 남기기 위해 사용했습니다.
- `next-slice-triage`: 검증 truth가 현재화된 뒤 다음 control을 operator stop이 아닌
  advisory tie-break로 좁히기 위해 사용했습니다.

## 변경 파일

변경 파일 - 없음. 이 라운드는 검증 및 control 작성 라운드이며 구현 파일은 수정하지
않았습니다.

## 확인한 대상

- `AGENTS.md`
- `.pipeline/harness/verify.md`
- `.pipeline/harness/council.md`
- `work/5/21/2026-05-21-claude-print-pipe-subcommand-fake-e2e-replay.md`
- `verify/5/21/2026-05-21-claude-print-pipe-opt-in-subcommand.md`
- `tests/test_pipeline_runtime_cli.py`
- `pipeline_runtime/cli.py`

## 재실행 검증

- `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py`
  - 결과: PASS, 출력 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_subcommand_fake_e2e_emits_wrapper_events`
  - 결과: PASS. `Ran 1 test in 0.010s`, `OK`.
- `python3 -m unittest -v tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_subcommand_fake_e2e_emits_wrapper_events tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_subcommand_calls_prompt_file_helper tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_subcommand_rejects_prompt_source_without_subprocess tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_from_prompt_file_accepts_local_utf8_file tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_prompt_source_rejects_invalid_inputs_without_subprocess tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_sends_prompt_and_feeds_stdout tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_returns_stderr_and_nonzero_exit tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_initializes_all_lanes_in_text_mode`
  - 결과: PASS. `Ran 8 tests in 0.041s`, `OK`.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_lane_vendor_command_keeps_claude_default_in_pane_text_mode`
  - 결과: PASS. `Ran 1 test in 0.004s`, `OK`.
- `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py work/5/21/2026-05-21-claude-print-pipe-subcommand-fake-e2e-replay.md`
  - 결과: PASS, 출력 없음.

## 코드 확인

- `tests/test_pipeline_runtime_cli.py`
  - `test_claude_print_jsonl_pipe_subcommand_fake_e2e_emits_wrapper_events`는 임시
    project root 아래 실제 UTF-8 prompt file과 Claude task hint를 만든 뒤
    `runtime_cli.main(["claude-print-jsonl-pipe", ...])`를 호출합니다.
  - 테스트는 `_run_claude_print_jsonl_pipe_from_prompt_file()` 또는
    `_run_claude_print_jsonl_pipe()`를 mock하지 않고 `runtime_cli.subprocess.Popen`만
    fake process로 대체합니다.
  - fake process는 prompt bytes를 stdin으로 받고, stdout JSONL을 반환하며,
    테스트는 command shape, `cwd`, wrapper event path, `DISPATCH_SEEN`,
    `TASK_ACCEPTED`, `TASK_DONE`, `READY`, task hint identity를 확인합니다.
- `pipeline_runtime/cli.py`
  - 이번 라운드에서 추가 생산 코드 수정은 없습니다.
  - `_lane_wrapper()`는 여전히 `_WrapperEmitter(..., jsonl_mode=False)`로 초기화되며
    `claude-print-jsonl-pipe` subcommand를 호출하지 않습니다.

## 실행하지 않은 검증

- live `claude` 실행, tmux/session access, controller/browser server, Playwright,
  full smoke, long soak는 실행하지 않았습니다.
- broad unittest 전체 묶음은 실행하지 않았습니다. 이번 변경은
  `tests/test_pipeline_runtime_cli.py`의 targeted fake replay에 한정됩니다.
- commit, push, branch/PR publication, PR creation, merge, release는 실행하지
  않았습니다.

## 런타임 표면

Prompt에 포함된 `RUNTIME_STATUS_AT_DISPATCH`를 권위 있는 dispatcher surface로
사용했습니다.

- `runtime_state: RUNNING`
- `automation_health: recovering`
- `automation_next_action: retrying`
- `active_control: .pipeline/implement_handoff.md#2085 implement`
- `turn_state: IDLE`
- `active_round: VERIFY_PENDING`

lane-local `status --json`, `doctor --json`, `tmux` 확인은 실행하지 않았고, 그
종류의 lane-local access mismatch를 operator boundary 근거로 사용하지 않았습니다.

## 판정

- 최신 `/work`의 구현 주장은 검증 완료입니다.
- Claude print-pipe 계열은 local foundation 기준으로 scaffold, prompt-source
  contract, explicit opt-in subcommand, fake e2e replay까지 확인됐습니다.
- 다음 단계는 계속 같은 family를 보강할지, current runtime docs/truth-sync로 넘길지,
  다른 dirty-bundle/current-risk 축으로 전환할지 우선순위가 갈립니다.
- advisory가 활성화돼 있고 real operator-only boundary는 없으므로, 다음 control은
  operator stop이 아니라 advisory tie-break가 맞습니다.

## 남은 리스크

- `claude-print-jsonl-pipe`는 local opt-in subcommand이며 supervisor default lane에
  연결되지 않았습니다.
- live Claude/tmux 검증은 계속 보류입니다.
- fake replay는 local unit evidence이며 full smoke, controller smoke, release-ready,
  publication-ready 근거가 아닙니다.
- 현재 worktree에는 이번 Claude print-pipe 계열 외 기존 dirty/untracked 항목이
  남아 있습니다.
- publication은 계속 held 상태입니다.

## 다음 컨트롤 판단

COUNCIL_DECISION: advisory_followup
REASON_CODE: next_slice_ambiguity_after_claude_print_pipe_fake_e2e
OWNER_ROLE: advisory
NEXT_CONTROL_FILE: .pipeline/advisory_request.md
NEXT_CONTROL_SEQ: 2086

EVIDENCE:
- `work/5/21/2026-05-21-claude-print-pipe-subcommand-fake-e2e-replay.md`
- `verify/5/21/2026-05-21-claude-print-pipe-subcommand-fake-e2e-replay.md`
- `tests/test_pipeline_runtime_cli.py`
- `pipeline_runtime/cli.py`
- `RUNTIME_STATUS_AT_DISPATCH`: `RUNNING`, `automation_health=recovering`,
  `automation_next_action=retrying`, `active_control=.pipeline/implement_handoff.md#2085 implement`

REJECTED:
- `.pipeline/operator_request.md`: destructive write, credential/auth,
  approval-record repair, truth-sync blocker, merge, release, external
  publication, or immediate safety boundary가 없습니다.
- `.pipeline/implement_handoff.md`: fake e2e replay까지 완료된 뒤에는 same-family
  hardening, runtime doc truth-sync, default wiring hold, 다른 dirty-bundle risk 중
  무엇이 우선인지 낮은 확신 상태입니다. advisory가 활성화돼 있으므로 implement
  owner에게 우선순위 판단을 넘기지 않습니다.
- default lane wiring/full smoke/release readiness: 현재 evidence는 explicit opt-in
  local fake evidence까지만 정당화하며 default lane 전환, full-smoke pass,
  release-ready, publication-ready 주장을 지원하지 않습니다.
- commit/push/PR handoff: implement prompt가 commit, push, branch/PR publication,
  PR creation, merge, release를 금지합니다.
