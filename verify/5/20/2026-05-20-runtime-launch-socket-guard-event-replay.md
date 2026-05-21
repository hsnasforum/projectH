STATUS: verified_with_followup
WORK: work/5/20/2026-05-20-runtime-launch-socket-guard-event-replay.md
PREVIOUS_VERIFY: verify/5/20/2026-05-20-runtime-launch-socket-guard-status-replay.md
NEXT_CONTROL_SEQ: 2013
ADVISORY_ENABLED: false

# 검증 기록

## 요약

`work/5/20/2026-05-20-runtime-launch-socket-guard-event-replay.md`에 기록된
supervisor event replay 테스트 추가는 현재 코드와 일치합니다.
`tests/test_pipeline_runtime_supervisor.py`에는
`test_record_status_events_preserves_local_socket_guard_automation_incident`가
추가되어 있으며, `_launch_failed_reason=LOCAL_SOCKET_GUARD_AUTO_HELD_REASON`이
`_record_status_events(status)`를 통해 `automation_incident` event payload에
`automation_health=attention`, `reason_code=local_socket_guard_auto_held`,
`incident_family=local_socket_guard_auto_held`, `next_action=verify_followup`로
남는지 확인합니다.

이번 검증은 deterministic unit replay입니다. 현재 file-backed runtime status는
여전히 `runtime_state=STARTING`, `automation_health=recovering`,
`automation_reason_code=runtime_starting`, `automation_next_action=retrying`이므로
live restart 성공, controller smoke 통과, release readiness는 주장하지 않습니다.

## 변경 파일

- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/20/2026-05-20-runtime-launch-socket-guard-event-replay.md`
- `verify/5/20/2026-05-20-runtime-launch-socket-guard-event-replay.md`

## 확인한 대상

- `work/5/20/2026-05-20-runtime-launch-socket-guard-event-replay.md`
- `verify/5/20/2026-05-20-runtime-launch-socket-guard-status-replay.md`
- `tests/test_pipeline_runtime_supervisor.py`
- `pipeline_runtime/supervisor.py`의 `run()` launch failure catch 경로
- `.pipeline/runs/20260520T061527Z-p65317/status.json`

## 실행한 검증

- `rg -n "test_record_status_events_preserves_local_socket_guard_automation_incident|automation_incident|LOCAL_SOCKET_GUARD_AUTO_HELD_REASON|verify_followup" tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS. 새 event replay와 핵심 assertion이 존재합니다.
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS. 출력 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_record_status_events_preserves_local_socket_guard_automation_incident tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_local_socket_guard_launch_failure_as_verify_followup`
  - 결과: PASS. 2개 테스트 통과.
- `git diff --check -- tests/test_pipeline_runtime_supervisor.py work/5/20/2026-05-20-runtime-launch-socket-guard-event-replay.md`
  - 결과: PASS. 출력 없음.
- `git diff --check --no-index -- /dev/null work/5/20/2026-05-20-runtime-launch-socket-guard-event-replay.md`
  - 결과: PASS. 새 파일 diff로 exit code는 1이지만 whitespace error 출력은 없었습니다.
- `sed -n '1,220p' .pipeline/runs/20260520T061527Z-p65317/status.json`
  - 결과: file-backed status는 `runtime_state=STARTING`,
    `automation_health=recovering`, `automation_reason_code=runtime_starting`,
    `automation_next_action=retrying`, active control
    `.pipeline/implement_handoff.md#2012`, active round `VERIFYING`입니다.

## 실행하지 않은 검증

- `python3 -m pipeline_runtime.cli start ...`, `tmux`, lane-local
  `status --json`, `doctor --json`는 실행하지 않았습니다.
  - 이유: dispatcher/file-backed runtime surface가 authoritative이며, 이번 검증은
    live socket 환경 접근 없이 unit replay로 닫는 범위입니다.
- controller Playwright, full smoke, release readiness, long soak는 실행하지 않았습니다.
  - 이유: browser-visible contract 변경이나 release claim이 아닙니다.
- commit, push, branch/PR publication, merge는 실행하지 않았습니다.

## 판정

- 최신 `/work`의 핵심 주장은 검증되었습니다.
- source 동작 변경 없이 supervisor automation event replay 테스트가 추가되었고, 테스트는 통과했습니다.
- 현재 runtime은 `STARTING/recovering/retrying`이므로 release-ready/full-smoke-pass를 주장하지 않습니다.
- 지금 필요한 경계는 operator stop이 아니라 실제 launch failure catch 경로의 unit replay입니다.

## Council 결정

COUNCIL_DECISION: implement
REASON_CODE: runtime_launch_socket_guard_launch_catch_replay
OWNER_ROLE: implement
NEXT_CONTROL_FILE: .pipeline/implement_handoff.md
NEXT_CONTROL_SEQ: 2013

EVIDENCE:
- `work/5/20/2026-05-20-runtime-launch-socket-guard-event-replay.md`
- `verify/5/20/2026-05-20-runtime-launch-socket-guard-event-replay.md`
- `tests/test_pipeline_runtime_supervisor.py`
- `pipeline_runtime/supervisor.py`
- `.pipeline/runs/20260520T061527Z-p65317/status.json`

REJECTED:
- operator_request: destructive/auth/credential/approval-truth-sync/publication/merge/safety stop이 현재 로컬 작업을 막고 있지 않습니다.
- advisory_request: `ADVISORY_ENABLED=false`이며 현재 증거로 하나의 bounded next slice를 정할 수 있습니다.
- reissue status/event replay: status JSON과 event payload 표면은 이번 검증으로 통과했으므로 같은 테스트를 반복하지 않습니다.
- live runtime restart/controller smoke: 현재 검증 범위를 넘어가며 socket 환경 충돌을 재유발할 수 있습니다.

## 남은 리스크

- current file-backed status는 아직 새 코드가 실제 runtime restart 경로에서 로드된 결과를 보여주지 않습니다.
- status JSON과 event stream은 보호되었지만, `run()`의 `_launch_runtime()` exception catch 경로가 local tmux socket permission denial을 canonical reason으로 설정하고 raw error를 `logs/launch-error.log`에 남기는지는 별도 replay로 확인하는 편이 안전합니다.
