# verify: 2026-05-21 Claude print pipe prompt source contract

## 대상 work

`work/5/21/2026-05-21-claude-print-pipe-prompt-source-contract.md`

## 이전 verify

`verify/5/21/2026-05-21-claude-print-pipe-wrapper-scaffold.md`

## 검증 결과

`VERIFY_DONE`.

최신 `/work`의 핵심 주장인 local-only prompt-source contract 추가, 명시
`allowed_root` 아래 UTF-8 prompt 파일만 허용, missing/directory/empty/out-of-root
거부, 허용 prompt text의 `_run_claude_print_jsonl_pipe()` 전달, 거부 입력에서
subprocess 미호출, 기존 pane-text lane 기본 동작 미변경은 현재 코드와 재실행 검증
기준으로 사실입니다.

## 사용 skill

- `round-handoff`: 최신 구현 closeout을 코드와 targeted 검증으로 재확인하고
  `/verify` 기록을 남기기 위해 사용했습니다.
- `next-slice-triage`: 검증 truth가 현재화된 뒤 다음 control을 operator stop이나
  advisory 재요청 없이 하나로 좁히기 위해 사용했습니다.

## 변경 파일

변경 파일 - 없음. 이 라운드는 검증 및 control 작성 라운드이며 구현 파일은 수정하지
않았습니다.

## 확인한 대상

- `AGENTS.md`
- `.pipeline/harness/verify.md`
- `.pipeline/harness/council.md`
- `work/5/21/2026-05-21-claude-print-pipe-prompt-source-contract.md`
- `verify/5/21/2026-05-21-claude-print-pipe-wrapper-scaffold.md`
- `.pipeline/advisory_request.md`
- `.pipeline/advisory_advice.md`
- `report/gemini/2026-05-21-claude-print-pipe-prompt-source-contract.md`
- `pipeline_runtime/cli.py`
- `tests/test_pipeline_runtime_cli.py`

## 재실행 검증

- `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py`
  - 결과: PASS, 출력 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_from_prompt_file_accepts_local_utf8_file tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_prompt_source_rejects_invalid_inputs_without_subprocess tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_sends_prompt_and_feeds_stdout tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_print_jsonl_pipe_returns_stderr_and_nonzero_exit tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_initializes_all_lanes_in_text_mode`
  - 결과: PASS. `Ran 5 tests in 0.023s`, `OK`.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_lane_vendor_command_keeps_claude_default_in_pane_text_mode`
  - 결과: PASS. `Ran 1 test in 0.005s`, `OK`.
- `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py work/5/21/2026-05-21-claude-print-pipe-prompt-source-contract.md`
  - 결과: PASS, 출력 없음.

## 코드 확인

- `pipeline_runtime/cli.py`
  - `ClaudePrintPromptSourceError`는 거부 code와 해석된 path를 보존합니다.
  - `_resolve_claude_print_prompt_path()`는 상대 경로를 `allowed_root` 아래로 해석하고,
    `resolve(strict=False)` 뒤 `relative_to(root)`로 root 밖 경로를 거부합니다.
  - `_load_claude_print_jsonl_prompt()`는 missing file, directory, whitespace-only
    prompt를 거부하고 UTF-8 text만 반환합니다.
  - `_run_claude_print_jsonl_pipe_from_prompt_file()`는 허용된 prompt text만
    `_run_claude_print_jsonl_pipe()`로 전달하며 기본 `cwd`는 해석된 root입니다.
  - `_lane_wrapper()`는 여전히 `_WrapperEmitter(..., jsonl_mode=False)`로 초기화되고
    prompt-file helper를 호출하지 않습니다.
- `tests/test_pipeline_runtime_cli.py`
  - 허용 prompt 파일이 `_run_claude_print_jsonl_pipe()`로 전달되는지 확인합니다.
  - missing/directory/empty/out-of-root 입력이 `ClaudePrintPromptSourceError`로
    거부되고 `_run_claude_print_jsonl_pipe()` 및 `subprocess.Popen`을 호출하지
    않는지 확인합니다.
  - 기존 fake subprocess Claude print-pipe 테스트와 lane text-mode 테스트가 계속
    통과합니다.

## 실행하지 않은 검증

- live `claude` 실행, tmux/session access, controller/browser server, Playwright,
  full smoke, long soak는 실행하지 않았습니다.
- broad unittest 전체 묶음은 실행하지 않았습니다. 이번 변경은 inactive scaffold의
  prompt-source contract와 해당 targeted tests에 한정됩니다.
- commit, push, branch/PR publication, PR creation, merge, release는 실행하지
  않았습니다.

## 런타임 표면

Prompt에 포함된 `RUNTIME_STATUS_AT_DISPATCH`를 권위 있는 dispatcher surface로
사용했습니다.

- `runtime_state: RUNNING`
- `automation_health: recovering`
- `automation_next_action: retrying`
- `active_control: .pipeline/implement_handoff.md#2083 implement`
- `turn_state: IDLE`
- `active_round: VERIFY_PENDING`

lane-local `status --json`, `doctor --json`, `tmux` 확인은 실행하지 않았고, 그
종류의 lane-local access mismatch를 operator boundary 근거로 사용하지 않았습니다.

## 판정

- 최신 `/work`의 구현 주장은 검증 완료입니다.
- 이번 변경은 foundation-only이며 active/default lane behavior를 열지 않았습니다.
- advisory가 앞서 `claude_print_pipe_opt_in_contract`를 거절한 이유는 prompt-source
  boundary 부재였고, 이번 `/work`에서 그 선행 조건이 충족됐습니다.
- 따라서 다음 control은 operator stop이나 advisory 재요청이 아니라 bounded implement
  slice로 좁힐 수 있습니다.

## 남은 리스크

- Claude print JSONL pipe는 아직 `_lane_wrapper()` 기본 경로와 supervisor 기본 command에
  연결되지 않은 explicit/inactive helper입니다.
- live Claude/tmux 검증은 계속 보류이며, 다음 slice도 fake subprocess/local file
  검증에 머물러야 합니다.
- 현재 worktree에는 이번 Claude print-pipe 계열 외 기존 dirty/untracked 항목이
  남아 있습니다.
- publication은 계속 held 상태입니다.

## 다음 컨트롤 판단

COUNCIL_DECISION: implement
REASON_CODE: claude_print_pipe_opt_in_contract_after_prompt_source
OWNER_ROLE: implement
NEXT_CONTROL_FILE: .pipeline/implement_handoff.md
NEXT_CONTROL_SEQ: 2084

EVIDENCE:
- `work/5/21/2026-05-21-claude-print-pipe-prompt-source-contract.md`
- `verify/5/21/2026-05-21-claude-print-pipe-prompt-source-contract.md`
- `.pipeline/advisory_advice.md`
- `report/gemini/2026-05-21-claude-print-pipe-prompt-source-contract.md`
- `pipeline_runtime/cli.py`
- `tests/test_pipeline_runtime_cli.py`
- `RUNTIME_STATUS_AT_DISPATCH`: `RUNNING`, `automation_health=recovering`,
  `automation_next_action=retrying`, `active_control=.pipeline/implement_handoff.md#2083 implement`

REJECTED:
- `.pipeline/operator_request.md`: destructive write, credential/auth,
  approval-record repair, truth-sync blocker, merge, release, external
  publication, or immediate safety boundary가 없습니다.
- `.pipeline/advisory_request.md`: advisory는 이미 prompt-source 선행 조건을 권고했고
  그 조건이 검증됐으므로 같은 family의 다음 정확한 slice를 다시 advisory로 보내지
  않아도 됩니다.
- default lane wiring/full smoke/release readiness: 현재 evidence는 explicit opt-in
  contract까지만 정당화하며 default lane 전환, full-smoke pass, release-ready,
  publication-ready 주장을 지원하지 않습니다.
- commit/push/PR handoff: implement prompt가 commit, push, branch/PR publication,
  PR creation, merge, release를 금지합니다.
