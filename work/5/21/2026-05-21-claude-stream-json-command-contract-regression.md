# 2026-05-21 Claude stream-json command contract regression

## 변경 파일

- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/21/2026-05-21-claude-stream-json-command-contract-regression.md`

## 사용 skill

- `security-gate`: Claude lane vendor command가 shell 실행 계약에 닿으므로, live binary 실행 없이 로컬 unit regression만 추가하는 경계인지 확인했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- Step 3 `Claude stream-json wrapper integration`은 `_lane_vendor_command("Claude")` 수동 확인을 기록했지만, 기본 Claude command가 `--output-format stream-json`을 계속 포함하는지 고정하는 supervisor unit regression은 없었습니다.
- 환경변수 lane command override가 있을 때는 운영자가 지정한 command를 그대로 우선해야 하므로, stream-json flag를 강제로 붙이지 않는 계약도 함께 잠갔습니다.

## 핵심 변경

- `test_lane_vendor_command_adds_stream_json_for_claude_default`를 추가했습니다.
- 새 테스트는 `_find_cli_bin`을 mock 처리하고 live `claude` binary를 실행하지 않은 채 기본 command가 `exec "/usr/bin/claude" --dangerously-skip-permissions --output-format stream-json`인지 확인합니다.
- `test_lane_vendor_command_prefers_env_override_for_claude_without_forcing_stream_json`를 추가했습니다.
- Claude override command가 설정된 경우 override가 우선하고 `--output-format stream-json`이 강제로 추가되지 않는지 확인합니다.
- `pipeline_runtime/supervisor.py`는 수정하지 않았습니다. 현재 production code가 새 regression을 통과했습니다.

## 검증

- `python3 -m py_compile tests/test_pipeline_runtime_supervisor.py`
  - 통과했습니다.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_lane_vendor_command_prefers_env_override_template tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_lane_vendor_command_prefers_env_override_for_claude_without_forcing_stream_json tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_lane_vendor_command_adds_stream_json_for_claude_default tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_lane_vendor_command_uses_yolo_for_gemini`
  - 통과했습니다. `Ran 4 tests in 0.009s`, `OK`.
- `git diff --check -- tests/test_pipeline_runtime_supervisor.py pipeline_runtime/supervisor.py work/5/21/`
  - 통과했습니다. 출력 없음.

## 남은 리스크

- live Claude runtime 검증은 실행하지 않았습니다. 실제 Claude binary의 `--output-format stream-json` 지원 여부와 live JSONL 출력은 이번 local unit regression 범위 밖입니다.
- `pipeline_runtime/supervisor.py`는 변경하지 않아 별도 `py_compile pipeline_runtime/supervisor.py`는 실행하지 않았습니다.
- Playwright, controller smoke, full smoke, long soak는 실행하지 않았습니다.
- commit, push, branch/PR publication, PR creation, merge, release는 실행하지 않았고 계속 held 상태입니다.
