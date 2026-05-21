# 2026-05-21 Pipeline launcher Task 1 bugfixes

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `pipeline_runtime/cli.py`
- `pipeline_runtime/automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_pipeline_runtime_cli.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `work/5/21/2026-05-21-pipeline-launcher-task1-bugfixes.md`

## 사용 skill

- `security-gate`: launcher/runtime control, tmux doctor, runtime event logging, compat text file write 경로가 바뀌므로 로컬 우선성과 감사 가능성을 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실패 확인, 검증 결과, 잔여 리스크를 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- `docs/superpowers/plans/2026-05-21-pipeline-launcher-bugfixes.md`의 Task 1 범위에 따라 P6/P9/P10/P14/P15/P17 단순 버그를 닫았습니다.
- 계획서의 `superpowers:*` skill 지시는 현재 Codex 세션의 사용 가능한 skill 목록에 없어 적용하지 못했고, 대신 Task 1의 파일 범위와 검증 절차를 그대로 따랐습니다.

## 핵심 변경

- P9: `doctor`의 `tmux_session` 체크가 tmux 세션 부재 시 `ok`가 아니라 `warn`과 start hint를 반환하게 했습니다.
- P17: `automation_incident_family()`가 known reason family는 보존하되, 정의되지 않은 reason code는 빈 문자열 family로 반환하게 했습니다.
- P10: lane command override template format에서 알 수 없는 key가 나오면 미해석 템플릿을 셸에 넘기지 않고 `lane_command_override_invalid` 이벤트를 남긴 뒤 `""`를 반환하게 했습니다.
- P14: `_reconcile_receipts()`의 단일 항목 `for job_state in [latest_job]` 루프를 제거하고 동일 로직을 단일 job 처리 구조로 정리했습니다.
- P15: `_refresh_control_seq_age()`의 광범위한 `except Exception`이 조용히 삼키지 않고 `control_seq_age_error` 이벤트를 남기게 했습니다.
- P6: `latest-work.txt`와 `latest-verify.txt` 쓰기를 직접 `write_text()`에서 공용 `atomic_write_text()` temp+rename 경로로 바꿨습니다.

## 검증

- 수정 전 실패 확인:
  - `python3 -m unittest -v tests.test_pipeline_runtime_cli.SupervisorCliTest.test_doctor_reports_tmux_warn_when_session_missing tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_unknown_reason_code_returns_empty_family tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_lane_command_override_format_key_error_returns_empty_and_logs_event tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_refresh_control_seq_age_logs_error_when_scan_fails tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_compat_files_uses_atomic_pattern_for_text_files`
  - 결과: P9/P17/P10/P6은 실패, P15는 이벤트 파일 부재로 오류가 나며 수정 필요를 확인했습니다.
- 수정 후 신규 회귀 테스트 확인:
  - 같은 5개 테스트 재실행 결과 `Ran 5 tests in 0.015s` / `OK`.
- 지정 컴파일 확인:
  - `python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/cli.py pipeline_runtime/automation_health.py`
  - 통과했습니다.
- 지정 전체 테스트 확인:
  - `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_automation_health -v`
  - 1차 실행은 P17을 unknown-only가 아니라 known reason까지 빈 family로 만든 회귀 때문에 7개 실패했습니다.
  - known reason allowlist를 보존하도록 수정한 뒤 재실행했고 `Ran 260 tests in 1.269s` / `OK`.
- whitespace 확인:
  - `git diff --check -- pipeline_runtime/supervisor.py pipeline_runtime/cli.py pipeline_runtime/automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_cli.py tests/test_pipeline_runtime_automation_health.py work/5/21`
  - closeout 작성 전후 모두 통과했습니다.

## 남은 리스크

- Task 2, Task 3, Task 4는 건드리지 않았습니다.
- Playwright, E2E, 전체 smoke, live runtime start/stop 검증은 범위 밖이라 실행하지 않았습니다.
- 이번 변경은 runtime control과 local compat 파일 쓰기 경로를 다루지만, 외부 publication, branch/PR, merge, release는 수행하지 않았습니다.
- 작업 시작 시점부터 대상 파일들은 이미 dirty 상태였고, 이번 기록은 Task 1 범위의 변경과 검증만 설명합니다.
- commit, push, PR publish, merge는 수행하지 않았습니다.
