STATUS: verified_with_followup
WORK: work/5/20/2026-05-20-runtime-launch-socket-guard-surface.md
PREVIOUS_VERIFY: verify/5/20/2026-05-20-automation-meta-loop-operator-hold.md
NEXT_CONTROL_SEQ: 2011
ADVISORY_ENABLED: false

# 검증 기록

## 요약

`work/5/20/2026-05-20-runtime-launch-socket-guard-surface.md`에 기록된
local tmux socket permission denial 표면화 변경은 코드, 테스트, 문서에서
확인되었습니다. `local_socket_guard_auto_held`는 `automation_health`의
verify follow-up reason에 포함되어 있고, `RuntimeSupervisor`의 launch 실패
분류는 tmux socket `Operation not permitted`를 generic
`runtime_launch_failed:RuntimeError` 대신 canonical reason으로 변환합니다.

다만 현재 file-backed runtime status는 여전히 `runtime_state=STARTING`,
`automation_health=recovering`, `automation_reason_code=runtime_starting`,
`automation_next_action=retrying`입니다. 이번 검증은 live restart, tmux 접근,
controller smoke, release readiness를 주장하지 않습니다.

## 변경 파일

- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `pipeline_runtime/automation_health.py`
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/20/2026-05-20-runtime-launch-socket-guard-surface.md`
- `verify/5/20/2026-05-20-runtime-launch-socket-guard-surface.md`

## 확인한 대상

- `pipeline_runtime/automation_health.py`
  - `LOCAL_SOCKET_GUARD_AUTO_HELD_REASON`
  - `VERIFY_FOLLOWUP_REASONS`
  - `BROKEN + local_socket_guard_auto_held` branch
- `pipeline_runtime/supervisor.py`
  - `_is_local_tmux_socket_permission_denial`
  - `_runtime_launch_failure_reason`
  - `_write_status()`의 `derive_automation_health(status)` 호출 지점
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `.pipeline/runs/20260520T061527Z-p65317/status.json`

## 실행한 검증

- `rg -n "LOCAL_SOCKET_GUARD_AUTO_HELD_REASON|local_socket_guard_auto_held|_runtime_launch_failure_reason|_is_local_tmux_socket_permission_denial|derive_automation_health|VERIFY_FOLLOWUP_REASONS" ...`
  - 결과: PASS. 코드, 테스트, 문서에 canonical reason과 classifier/health 경로가 존재합니다.
- `python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_automation_health.py`
  - 결과: PASS. 출력 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_broken_local_socket_guard_routes_to_verify_followup tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_generic_broken_runtime_still_requires_operator tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_runtime_launch_failure_reason_classifies_tmux_socket_permission_denial tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_runtime_launch_failure_reason_keeps_generic_runtime_errors`
  - 결과: PASS. 4개 테스트 통과.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health`
  - 결과: PASS. 43개 테스트 통과.
- `git diff --check -- pipeline_runtime/supervisor.py pipeline_runtime/automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_automation_health.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md work/5/20/2026-05-20-runtime-launch-socket-guard-surface.md`
  - 결과: PASS. 출력 없음.
- `git diff --check --no-index -- /dev/null work/5/20/2026-05-20-runtime-launch-socket-guard-surface.md`
  - 결과: PASS. 새 파일 diff로 exit code는 1이지만 whitespace error 출력은 없었습니다.
- `sed -n '1,220p' .pipeline/runs/20260520T061527Z-p65317/status.json`
  - 결과: file-backed status는 `runtime_state=STARTING`,
    `automation_health=recovering`, `automation_reason_code=runtime_starting`,
    `automation_next_action=retrying`, active control
    `.pipeline/implement_handoff.md#2010`, active round `VERIFYING`입니다.

## 실행하지 않은 검증

- `python3 -m pipeline_runtime.cli start ...`, `tmux`, lane-local
  `status --json`, `doctor --json`는 실행하지 않았습니다.
  - 이유: 현재 지시는 dispatcher/file-backed runtime surface를 authoritative로
    사용하라고 지정했고, lane-local tmux/socket 접근 충돌만으로 operator stop을
    만들지 말라고 했습니다.
- controller Playwright, full smoke, release readiness 검증은 실행하지 않았습니다.
  - 이유: 이번 변경은 runtime helper/status 분류와 문서 동기화이며 browser-visible
    product contract 변경이 아닙니다.
- commit, push, branch/PR publication, merge는 실행하지 않았습니다.

## 판정

- 최신 `/work`의 핵심 주장은 검증되었습니다.
- local socket guard는 generic runtime-broken operator stop으로 과분류하지 않고
  verify follow-up 계열로 라우팅되도록 helper/unit 수준에서 보호됩니다.
- 현재 runtime은 `STARTING/recovering/retrying` 상태이므로 full-smoke pass나
  release-ready는 주장하지 않습니다.
- 지금 필요한 경계는 operator stop이 아니라 같은 incident family의 작은
  감독자 status export 재현 테스트입니다.

## Council 결정

COUNCIL_DECISION: implement
REASON_CODE: runtime_launch_socket_guard_status_replay
OWNER_ROLE: implement
NEXT_CONTROL_FILE: .pipeline/implement_handoff.md
NEXT_CONTROL_SEQ: 2011

EVIDENCE:
- `work/5/20/2026-05-20-runtime-launch-socket-guard-surface.md`
- `verify/5/20/2026-05-20-runtime-launch-socket-guard-surface.md`
- `.pipeline/runs/20260520T061527Z-p65317/status.json`
- `pipeline_runtime/supervisor.py`
- `pipeline_runtime/automation_health.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`

REJECTED:
- operator_request: 현재 destructive/auth/credential/approval-truth-sync/publication/merge/safety stop이 로컬 작업을 막고 있지 않습니다.
- advisory_request: `ADVISORY_ENABLED=false`이며 현재 증거로 하나의 bounded next slice를 정할 수 있습니다.
- live runtime restart or controller smoke: 현재 slice의 검증 범위를 넘어가고 socket 환경 충돌을 재유발할 수 있습니다.

## 남은 리스크

- current file-backed status는 아직 새 코드가 실제 runtime restart 경로에서 로드된
  결과를 보여주지 않습니다.
- 현재 테스트는 classifier와 automation-health helper를 직접 보호하지만,
  `_launch_failed_reason=local_socket_guard_auto_held`가 `_write_status()`를 통해
  status JSON의 `automation_health_source`까지 일관되게 표면화되는 감독자 통합
  replay는 별도 한정 테스트로 닫는 편이 안전합니다.
