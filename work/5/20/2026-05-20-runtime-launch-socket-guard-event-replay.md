# 2026-05-20 runtime launch socket guard event replay

## 변경 파일

- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/20/2026-05-20-runtime-launch-socket-guard-event-replay.md`

## 사용 skill

- `security-gate`: local tmux socket permission denial이 runtime event stream에 남는 경계를 다루므로 operator routing, local path 노출, log/event payload 경계를 확인하기 위해 사용했습니다.
- `work-log-closeout`: handoff 실행 결과, 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#2012`는 `local_socket_guard_auto_held`가 `_write_status()` status JSON뿐 아니라 `_record_status_events(status)`의 `automation_incident` event payload에도 같은 reason/action으로 보존되는지 확인하라고 지시했습니다.
- 직전 status replay는 `automation_health_source` 표면을 닫았지만 event stream payload는 별도 assertion이 없었습니다.
- 이번 라운드는 live runtime restart나 tmux 접근 없이 deterministic unit test로 event payload만 재현하는 한정 보강입니다.

## 핵심 변경

- `tests/test_pipeline_runtime_supervisor.py`에 `test_record_status_events_preserves_local_socket_guard_automation_incident`를 추가했습니다.
- 테스트는 `RuntimeSupervisor(..., start_runtime=False)`와 `_launch_failed_reason=LOCAL_SOCKET_GUARD_AUTO_HELD_REASON`를 사용합니다.
- live tmux/socket 접근 없이 watcher, session, lane status, artifacts를 mock 처리했습니다.
- `_write_status()` 뒤 `_record_status_events(status)`를 호출하고 `supervisor.events_path`의 `automation_incident` event를 읽어 검증합니다.
- event payload가 `automation_health=attention`, `reason_code=local_socket_guard_auto_held`, `incident_family=local_socket_guard_auto_held`, `next_action=verify_followup`을 보존하는지 확인합니다.
- source 동작 변경은 없었습니다. 이번 handoff에서 필요한 보강은 테스트 추가로 충족되었습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA `d12a960085e347c209648a9a70362238ccbe301a7be44c4a9b615b74f9bf2bb3`와 일치했습니다.
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_record_status_events_preserves_local_socket_guard_automation_incident tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_local_socket_guard_launch_failure_as_verify_followup`
  - 결과: PASS. 2개 테스트 통과.
- `git diff --check -- tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS. 출력 없음.
- `git diff --check --no-index -- /dev/null work/5/20/2026-05-20-runtime-launch-socket-guard-event-replay.md`
  - 결과: PASS. diff 존재로 exit code는 1이지만 whitespace error 출력은 없었습니다.

## 남은 리스크

- `pipeline_runtime/supervisor.py`는 변경하지 않았으므로 handoff의 조건부 classifier regression 재실행은 필요하지 않았습니다.
- live `python3 -m pipeline_runtime.cli start ...`, `tmux`, lane-local `status --json`, `doctor --json`는 실행하지 않았습니다. handoff가 runtime restart와 lane-local socket 접근을 금지했고, 이번 범위는 deterministic unit replay입니다.
- controller Playwright/webServer/full-smoke, release readiness, long soak는 실행하지 않았습니다. browser-visible contract 변경이나 release claim이 아닙니다.
- 작업 시작 전부터 `tests/test_pipeline_runtime_supervisor.py`에는 이전 라운드의 dirty 변경이 있었습니다. 이번 라운드에서 직접 추가한 것은 `_record_status_events()` local socket guard event replay 테스트입니다.
- raw launch error의 local socket path는 계속 canonical reason code가 아니라 launch error log에만 보존되어야 합니다. 이번 테스트는 이 경계를 바꾸지 않았습니다.
- commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 수행하지 않았습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았습니다.
