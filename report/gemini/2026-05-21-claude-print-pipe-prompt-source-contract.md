# 2026-05-21 Claude print pipe prompt source contract

## 요청

- Request: `.pipeline/advisory_request.md`
- Based on work: `work/5/21/2026-05-21-claude-print-pipe-wrapper-scaffold.md`
- Based on verify: `verify/5/21/2026-05-21-claude-print-pipe-wrapper-scaffold.md`
- Advice control: `2082`

## 판정

`RECOMMEND: implement`

다음 slice는 `claude_print_pipe_prompt_source_contract`가 맞습니다.

## 근거

- 현재 scaffold는 inactive/non-default helper이며, `prompt: str`를 직접 받아
  `claude --print --verbose --output-format stream-json` stdin으로 보냅니다.
- task hint는 현재 active task identity와 `control_seq`를 운반하지만, prompt 본문
  source contract는 아닙니다.
- opt-in 실행 경로를 먼저 열면 어떤 로컬 기록의 어떤 prompt를 stdin으로 넣을지
  경계가 불명확합니다.
- prompt-source contract를 먼저 고정하면 이후 opt-in wiring을 더 작고 검증 가능하게
  만들 수 있습니다.

## 권고 slice

Implement owner에게 다음 한 slice만 넘기는 것을 권고합니다.

- Target files:
  - `pipeline_runtime/cli.py`
  - `tests/test_pipeline_runtime_cli.py`
  - 필요 시 `work/5/21/<new-closeout>.md`
- Add a local helper that loads Claude print-pipe prompt text only from an
  explicitly provided UTF-8 prompt file/path contract.
- The helper should reject missing files, directories, empty prompt text, and
  paths outside the intended local project/runtime boundary.
- Add fake/file tests proving accepted prompt text is passed to
  `_run_claude_print_jsonl_pipe()` and rejected inputs do not invoke subprocess.
- Keep `_lane_wrapper()`, `_lane_vendor_command()`, active profile, tmux, live
  `claude`, controller/browser, and publication behavior unchanged.

## 거절한 후보

- `claude_print_pipe_opt_in_contract`: 아직 prompt source boundary가 없으므로
  opt-in 실행 경로를 먼저 여는 것은 순서가 이릅니다.
- `switch_to_different_safe_local_dirty_bundle_slice`: 이번 request/work/verify의
  named evidence만으로는 Claude wrapper family보다 우선할 근거가 부족합니다.
- operator request: destructive write, credential/auth, approval-record repair,
  truth-sync blocker, merge/release/external publication, immediate safety
  boundary가 아닙니다.

## 검증 권고

- `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py`
- prompt-source helper targeted tests plus existing Claude print-pipe fake
  subprocess tests
- `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py work/5/21/`

## 금지 범위

- live `claude` 실행
- tmux/session access
- default lane behavior 변경
- controller/browser server, Playwright, full smoke, long soak
- commit, push, branch/PR publication, merge, release
- release-ready, full-smoke-pass, publication-ready 주장
