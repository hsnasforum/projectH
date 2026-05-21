# 2026-05-21 Claude stream-json wrapper integration

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `pipeline_runtime/cli.py`
- `tests/test_pipeline_runtime_cli.py`
- `work/5/21/2026-05-21-claude-stream-json-wrapper-integration.md`

## 사용 skill

- `security-gate`: Claude lane 실행 명령과 wrapper event 기록 경로가 shell/runtime control 및 로컬 로그 표면에 닿으므로, 주입 방어와 audit boundary를 확인했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- tmux pane text 추론 대신 Claude Code의 구조화 JSONL 출력을 wrapper event로 변환해, supervisor가 lane vendor별 출력 형식을 몰라도 같은 `wrapper_models` 경로를 읽도록 하기 위함입니다.
- Step 2에서 남은 `_build_lane_statuses()` fallback 브랜치의 `has_accepted_task` dead code를 함께 정리했습니다.

## 핵심 변경

- `_lane_vendor_command("Claude")`가 기본 Claude command에 `--output-format stream-json`을 추가합니다.
  - 기존 `--dangerously-skip-permissions` vendor arg는 유지합니다.
  - 환경변수 lane command override가 있으면 기존처럼 override를 우선합니다.
- `_WrapperEmitter`에 `jsonl_mode`를 추가했습니다.
  - Claude lane wrapper는 `jsonl_mode=True`로 초기화됩니다.
  - `{"type":"text","text":"..."}`와 `{"type":"tool_use",...}`는 `DISPATCH_SEEN` / `TASK_ACCEPTED`로 변환합니다.
  - `{"type":"result"}`와 stream EOF는 `TASK_DONE` 후 `READY`로 변환합니다.
- JSONL 파싱 실패 시 `jsonl_mode=False`로 전환하고 기존 text parser로 fallback합니다.
- Codex/Gemini의 기존 text parsing 경로는 `jsonl_mode=False`일 때 그대로 유지됩니다.
- `_build_lane_statuses()` pane fallback 내부의 도달 불가능한 `has_accepted_task` 분기를 제거했습니다.

## 검증

- focused 신규 테스트:
  - `python3 -m unittest -v tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_text_event_emits_task_accepted tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_tool_use_event_emits_task_accepted tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_result_event_emits_task_done tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_stream_finish_emits_task_done tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_jsonl_mode_false_keeps_codex_text_parsing`
  - 결과: `Ran 5 tests in 0.008s` / `OK`.
- fallback focused 테스트:
  - `python3 -m unittest -v tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_invalid_output_falls_back_to_text_parsing`
  - 결과: `Ran 1 test in 0.002s` / `OK`.
- Claude command 확인:
  - 임시 `RuntimeSupervisor`에서 `_lane_vendor_command("Claude")` 호출
  - 결과: `exec "/usr/bin/claude" --dangerously-skip-permissions --output-format stream-json`.
- 컴파일:
  - `python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/cli.py`
  - 통과했습니다.
- CLI 전체 테스트:
  - `bash -o pipefail -lc 'python3 -m unittest tests.test_pipeline_runtime_cli -v 2>&1 | tail -5'`
  - 결과: `Ran 44 tests in 0.132s` / `OK`.
- supervisor 전체 테스트:
  - `bash -o pipefail -lc 'python3 -m unittest tests.test_pipeline_runtime_supervisor -v 2>&1 | tail -5'`
  - 결과: `Ran 199 tests in 1.284s` / `OK`.
- whitespace 확인:
  - `git diff --check -- pipeline_runtime/supervisor.py pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py`
  - 통과했습니다.

## 남은 리스크

- live Claude Code binary로 실제 `--output-format stream-json` 실행은 수행하지 않았습니다. 미지원 버전이면 wrapper emitter가 JSONL 파싱 실패 시 text parser로 fallback합니다.
- Codex/Gemini lane은 의도적으로 변경하지 않았습니다.
- wrapper event schema 자체(`pipeline_runtime/wrapper_events.py`)는 이번 라운드에서 추가 수정하지 않았습니다.
- Unix socket IPC나 agent side-channel 확장은 범위 밖입니다.
- commit, push, PR, merge, publish는 수행하지 않았습니다.
