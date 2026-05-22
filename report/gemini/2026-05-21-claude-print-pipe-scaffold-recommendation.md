# 2026-05-21 Claude print pipe scaffold recommendation

## 요청

- Request: `.pipeline/advisory_request.md`
- Based on work: `work/5/21/2026-05-21-close-live-claude-stream-json-operator-gate.md`
- Based on verify: `verify/5/21/2026-05-21-close-live-claude-stream-json-operator-gate.md`
- Advice control: `2079`

## 판정

`RECOMMEND: implement`

다음 slice는 `claude_print_pipe_wrapper_local_scaffold`가 맞습니다.

## 근거

- live Claude stream-json gate는 `HOLD_LIVE_VALIDATION_LOCAL_ONLY`로 닫혔습니다.
- Case B가 확인됐습니다: tmux PTY에서 `--output-format stream-json`은 JSONL이 아니라
  Claude TUI를 출력합니다.
- 단기 교정은 이미 적용 및 검증됐습니다: Claude 기본 command는
  `--output-format stream-json`을 자동 추가하지 않고, lane wrapper는
  `jsonl_mode=False`로 초기화됩니다.
- 남은 같은-family 리스크는 `claude --print --verbose --output-format stream-json`
  stdin pipe 구조가 아직 코드로 고정되지 않았다는 점입니다.
- evidence-only refresh는 이미 같은 family에서 반복됐고, 이번 hold 이후 다시
  실행해도 새 current-risk reduction이 작습니다.
- 다른 dirty-bundle slice는 이번 request의 named evidence보다 넓고, advisory
  근거가 부족합니다.

## 권고 slice

Implement owner에게 다음 한 slice만 넘기는 것을 권고합니다.

- Target files:
  - `pipeline_runtime/cli.py`
  - `tests/test_pipeline_runtime_cli.py`
  - 필요 시 `work/5/21/<new-closeout>.md`
- Add a local, non-default Claude print JSONL pipe scaffold in
  `pipeline_runtime/cli.py`.
- The scaffold should build or execute the intended non-PTY command shape:
  `claude --print --verbose --output-format stream-json`, send prompt text via
  stdin, and feed stdout JSONL through the existing `_WrapperEmitter` JSONL path.
- Cover it with fake `subprocess.Popen` / fake stdout tests only.
- Do not wire it into `_lane_wrapper()` default behavior, `_lane_vendor_command()`,
  active agent profile, tmux, controller/browser flows, or live `claude`.

## 거절한 후보

- `post_revert_wrapper_runtime_local_evidence_refresh`: local aggregate evidence가
  이미 최신 gate close 전후 기록에 남아 있어 반복성이 큽니다.
- `choose_different_safe_local_dirty_bundle_slice`: 이번 advisory request의 named
  evidence만으로는 Claude wrapper family보다 우선할 근거가 부족합니다.
- operator request: destructive write, credential/auth, approval-record repair,
  truth-sync blocker, merge/release/external publication, immediate safety
  boundary가 아닙니다.

## 검증 권고

- `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py`
- 새 fake subprocess/stdin/stdout 테스트와 기존 Claude JSONL emitter targeted tests
- `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py work/5/21/`

## 금지 범위

- live `claude` 실행
- tmux/session access
- controller/browser server, Playwright, full smoke, long soak
- commit, push, branch/PR publication, merge, release
- release-ready, full-smoke-pass, publication-ready 주장
