# 2026-05-21 Claude print pipe rejection audit event contract

## 요청

- Request: `.pipeline/advisory_request.md`
- Based on work: `work/5/21/2026-05-21-claude-print-pipe-subcommand-fake-e2e-replay.md`
- Based on verify: `verify/5/21/2026-05-21-claude-print-pipe-subcommand-fake-e2e-replay.md`
- Advice control: `2087`

## 판정

`RECOMMEND: implement`

다음 slice는 `claude_print_pipe_rejection_audit_event_contract`가 맞습니다.

## 근거

- 현재 `claude-print-jsonl-pipe`는 explicit opt-in이고, fake e2e replay까지 검증됐습니다.
- `.pipeline/README.md`와 `.claude/rules/pipeline-runtime.md`의 현재 runtime-doc 표면은
  wrapper-events를 lane status의 primary truth로 둡니다.
- 현재 prompt-source rejection은 stderr와 return code `2`로 끝나지만, run-specific
  wrapper-events trace는 남기지 않습니다.
- opt-in subcommand가 이미 run-specific wrapper event directory를 만들기 때문에,
  rejection도 같은 local audit surface에 남기는 것이 docs truth-sync보다 직접적인
  current-risk reduction입니다.

## 권고 slice

Implement owner에게 다음 한 slice만 넘기는 것을 권고합니다.

- Target files:
  - `pipeline_runtime/cli.py`
  - `tests/test_pipeline_runtime_cli.py`
  - one Korean `/work` closeout under `work/5/21/`
- In `_claude_print_jsonl_pipe_command()`, when `ClaudePrintPromptSourceError`
  is caught, append an auditable wrapper event under the same run-specific
  `wrapper_dir` before printing stderr and returning `2`.
- Use existing `append_wrapper_event()` / task-hint helpers where possible:
  - if a valid active Claude task hint is available, emit `BRIDGE_DIAGNOSTIC`
    with `job_id`, `dispatch_id`, `control_seq`, `code=<exc.code>`, and
    `path=<exc.path>`.
  - otherwise emit `BROKEN` with `pid=0`, `reason="prompt_source_rejected"`,
    `code=<exc.code>`, and `path=<exc.path>`.
- Add local fake tests proving rejected prompt-source input writes the audit
  event and still does not invoke `_run_claude_print_jsonl_pipe()` or
  `subprocess.Popen`.
- Keep it explicit opt-in only: no live `claude`, tmux, `_lane_wrapper()`,
  `_lane_vendor_command()`, supervisor default command/profile, browser/full
  smoke, release, or publication changes.

## 거절한 후보

- `claude_print_pipe_runtime_doc_truth_sync`: the exact runtime docs inspected do
  not currently contradict the opt-in-only behavior; they instead support
  strengthening wrapper-event audit coverage first.
- `switch_to_different_safe_local_dirty_bundle_slice`: the request/work/verify
  packet does not name clearer current-risk evidence outside the Claude
  print-pipe family.
- `operator_required`: no destructive write, credential/auth, approval-record
  repair, truth-sync blocker, merge/release/external publication, or immediate
  safety boundary blocks local work now.

## 검증 권고

- `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py`
- the new rejection audit event tests
- existing `claude-print-jsonl-pipe` subcommand tests and fake e2e replay test
- existing prompt-source helper and Claude print-pipe fake subprocess tests
- `tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_initializes_all_lanes_in_text_mode`
- `tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_lane_vendor_command_keeps_claude_default_in_pane_text_mode`
- `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py work/5/21/`

## 금지 범위

- live `claude` execution
- tmux/session access
- default lane behavior changes
- controller/browser server, Playwright, full smoke, long soak
- commit, push, branch/PR publication, merge, release
- release-ready, full-smoke-pass, publication-ready claims
