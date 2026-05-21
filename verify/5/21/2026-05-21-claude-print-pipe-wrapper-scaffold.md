# verify: 2026-05-21 Claude print pipe wrapper scaffold

## 대상 work

`work/5/21/2026-05-21-claude-print-pipe-wrapper-scaffold.md`

## 이전 verify

`verify/5/21/2026-05-21-close-live-claude-stream-json-operator-gate.md`

## 검증 결과

`VERIFY_DONE`.

최신 `/work`의 핵심 주장인 inactive/non-default Claude print JSONL pipe
scaffold 추가, fake subprocess/stdin/stdout 테스트 추가, 기본 lane wrapper와
Claude default command 미변경은 현재 코드와 재실행 검증 기준으로 사실입니다.

## 사용 skill

- `round-handoff`: 최신 구현 closeout을 코드와 테스트 결과로 재확인하고 `/verify`
  기록을 남기기 위해 사용했습니다.
- `next-slice-triage`: 검증 truth가 현재화된 뒤 operator stop이 아닌 다음 control을
  고르기 위해 사용했습니다.

## 확인한 대상

- `AGENTS.md`
- `.pipeline/harness/verify.md`
- `.pipeline/harness/council.md`
- `work/5/21/2026-05-21-claude-print-pipe-wrapper-scaffold.md`
- `verify/5/21/2026-05-21-close-live-claude-stream-json-operator-gate.md`
- `pipeline_runtime/cli.py`
- `tests/test_pipeline_runtime_cli.py`

## 재실행 검증

- `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py`
  - 결과: PASS, 출력 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_sends_prompt_and_feeds_stdout tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_returns_stderr_and_nonzero_exit tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_text_event_emits_task_accepted tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_tool_use_event_emits_task_accepted tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_result_event_emits_task_done tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_stream_finish_emits_task_done tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_invalid_output_falls_back_to_text_parsing tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_initializes_all_lanes_in_text_mode`
  - 결과: PASS. `Ran 8 tests in 0.041s`, `OK`.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_lane_vendor_command_keeps_claude_default_in_pane_text_mode`
  - 결과: PASS. `Ran 1 test in 0.003s`, `OK`.
- `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py work/5/21/`
  - 결과: PASS, 출력 없음.

## 코드 확인

- `pipeline_runtime/cli.py`
  - `_CLAUDE_PRINT_JSONL_ARGS`는 `("--print", "--verbose", "--output-format", "stream-json")`입니다.
  - `_run_claude_print_jsonl_pipe()`는 `subprocess.Popen()`에 `stdin`,
    `stdout`, `stderr`를 `PIPE`로 넘기고 prompt를 UTF-8 bytes로 `communicate()`에
    전달합니다.
  - stdout은 `_WrapperEmitter(lane_name="Claude", jsonl_mode=True)`에 전달되고,
    stderr는 별도 문자열로 반환됩니다.
  - `_lane_wrapper()` 기본 흐름은 이 helper를 호출하지 않으며 기존
    `jsonl_mode=False` 초기화를 유지합니다.
- `tests/test_pipeline_runtime_cli.py`
  - 새 fake process 테스트가 prompt stdin 전달, command shape, stdout JSONL 이벤트,
    stderr/nonzero returncode 반환을 확인합니다.
  - 기존 Claude JSONL emitter targeted tests가 계속 통과합니다.

## 실행하지 않은 검증

- live `claude` 실행, tmux/session access, controller/browser server, Playwright,
  full smoke, long soak는 실행하지 않았습니다.
- broad unittest 전체 묶음은 실행하지 않았습니다. 이번 변경은 `pipeline_runtime/cli.py`
  scaffold와 해당 targeted tests에 한정됩니다.
- commit, push, branch/PR publication, PR creation, merge, release는 실행하지
  않았습니다.

## 런타임 표면

Prompt에 포함된 `RUNTIME_STATUS_AT_DISPATCH`를 권위 있는 dispatcher surface로
사용했습니다.

- `runtime_state: RUNNING`
- `automation_health: recovering`
- `automation_next_action: retrying`
- `active_control: .pipeline/implement_handoff.md#2080 implement`
- `turn_state: IDLE`
- `active_round: VERIFY_PENDING`

lane-local `status --json`, `doctor --json`, `tmux` 확인은 실행하지 않았고, 그
종류의 lane-local access mismatch를 operator boundary 근거로 사용하지 않았습니다.

## 판정

- 최신 `/work`의 구현 주장은 검증 완료입니다.
- 이번 scaffold는 foundation-only입니다. shipped default lane behavior는 여전히
  Claude pane text mode이며 live Claude stream-json pass나 release readiness를
  주장하지 않습니다.
- `HOLD_LIVE_VALIDATION_LOCAL_ONLY` 경계는 유지됩니다.

## 남은 리스크

- scaffold는 아직 `_lane_wrapper()`나 supervisor default command에 연결되지 않은
  inactive/non-default helper입니다.
- 다음 단계는 opt-in wiring, 추가 prompt-source contract, 또는 다른 local-risk
  slice 중 무엇을 먼저 할지 우선순위 판단이 필요합니다.
- 현재 worktree에는 이번 scaffold 밖의 기존 dirty 항목이 남아 있습니다.
- publication은 계속 held 상태입니다.

## 다음 컨트롤 판단

COUNCIL_DECISION: advisory_followup
REASON_CODE: next_slice_ambiguity_after_claude_print_pipe_scaffold
OWNER_ROLE: advisory
NEXT_CONTROL_FILE: .pipeline/advisory_request.md
NEXT_CONTROL_SEQ: 2081

EVIDENCE:
- `work/5/21/2026-05-21-claude-print-pipe-wrapper-scaffold.md`
- `verify/5/21/2026-05-21-claude-print-pipe-wrapper-scaffold.md`
- `pipeline_runtime/cli.py`
- `tests/test_pipeline_runtime_cli.py`
- `RUNTIME_STATUS_AT_DISPATCH`: `RUNNING`, `automation_health=recovering`,
  `automation_next_action=retrying`, `active_control=.pipeline/implement_handoff.md#2080 implement`

REJECTED:
- `.pipeline/operator_request.md`: no destructive write, credential/auth,
  approval-record repair, truth-sync blocker, merge, release, external
  publication, or immediate safety boundary blocks local work now.
- `.pipeline/implement_handoff.md`: after an inactive scaffold, the next local
  slice is ambiguous between opt-in wiring, prompt-source contract hardening,
  another same-family replay, or a different dirty-bundle risk. Advisory is
  enabled, so prioritization should not be pushed to the implement owner.
- commit/push/PR handoff: implement prompts forbid commit, push, branch/PR
  publication, PR creation, merge, and release.
- full smoke / release readiness handoff: current evidence does not support
  controller-smoke pass, full-smoke pass, release-ready, or publication-ready
  claims.
