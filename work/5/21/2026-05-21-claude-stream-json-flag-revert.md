# 2026-05-21 claude stream-json flag revert pane mode

## 변경 파일
- `pipeline_runtime/supervisor.py`
- `pipeline_runtime/cli.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_pipeline_runtime_cli.py`
- `work/5/21/2026-05-21-claude-stream-json-flag-revert-pane-mode.md`

## 사용 skill
- `security-gate`: Claude lane 실행 명령과 lane wrapper 초기화가 runtime control 경계와 publication 경계를 넘지 않는지 확인하기 위해 사용했습니다.
- `work-log-closeout`: CONTROL_SEQ 2109의 실제 변경, 검증, 남은 리스크를 `/work`에 남기기 위해 사용했습니다.

## 변경 이유
- `verify/5/21/2026-05-21-live-claude-stream-json-validation.md`에서 케이스 B가 확정됐습니다.
- Claude Code 2.1.146의 tmux PTY 인터랙티브 세션에서 `--output-format stream-json`은 JSONL을 출력하지 않고 TUI를 표시합니다.
- 따라서 Claude lane 기본 실행 명령에 `--output-format stream-json`을 붙이는 현재 구현은 유효하지 않으며, 실제로는 `_feed_jsonl()` 첫 파싱 실패 후 pane text fallback에 의존합니다.

## 핵심 변경
- `_lane_vendor_command("Claude")`에서 `--output-format stream-json` 자동 추가를 제거했습니다.
- `_lane_wrapper()`의 `_WrapperEmitter` 초기화는 모든 lane에서 `jsonl_mode=False`가 되도록 고정했습니다.
- `_WrapperEmitter.jsonl_mode`, `_feed_jsonl()`, `_on_claude_activity()` 등 JSONL 처리 코드는 삭제하지 않고 보존했습니다.
- Claude 기본 vendor command 테스트를 `stream-json` 추가 기대에서 pane text mode 유지 기대 테스트로 교체했습니다.
- 모든 lane wrapper가 text mode로 초기화되는 회귀 테스트를 추가했습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/cli.py`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_cli -v 2>&1 | tail -5`
  - 결과: `Ran 264 tests`, `OK`
- 통과: `python3 -c "... RuntimeSupervisor ... assert '--output-format' not in cmd ..."`
  - 결과: `OK: --output-format not in Claude command`
- 통과: `git diff --check -- pipeline_runtime/supervisor.py pipeline_runtime/cli.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_cli.py`
- 예정 확인: `git diff --check -- work/5/21/`
  - 이 note 작성 후 실행 대상입니다.

## 남은 리스크
- 이번 라운드는 단기 교정으로, `claude --print --verbose --output-format stream-json`을 stdin 파이프로 실행하는 별도 wrapper 구조는 구현하지 않았습니다.
- Claude lane은 의도적으로 기존 pane text 경로에 남아 있습니다.
- `jsonl_mode` 코드는 향후 `--print` 기반 구조 전환 시 재사용하기 위해 보존했습니다.
- commit, push, PR, merge, publish는 실행하지 않았습니다.
