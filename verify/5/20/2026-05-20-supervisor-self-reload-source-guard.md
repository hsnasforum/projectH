STATUS: verified_with_cli_runtime_reload_source_gap
WORK: work/5/20/2026-05-20-supervisor-self-reload-source-guard.md
PREVIOUS_VERIFY: verify/5/20/2026-05-20-automation-health-watcher-source-reload-guard.md
CONTROL_SEQ_NEXT: 2006
ADVISORY_ENABLED: false

# 검증 기록

## 요약

`work/5/20/2026-05-20-supervisor-self-reload-source-guard.md`의 핵심 주장은
검증됐습니다. `_WATCHER_SELF_RESTART_SOURCE_NAMES`에는
`pipeline_runtime/supervisor.py`가 추가됐고, 새 regression은 supervisor source가
`experimental.pid`보다 최신이면 `_watcher_source_restart_marker()`의
`source_path`가 `pipeline_runtime/supervisor.py`를 가리킴을 확인합니다.

`RUNTIME_STATUS_AT_DISPATCH`는 여전히 dispatcher authority로
`RUNNING + ok/continue`, `active_round=VERIFY_PENDING`, `turn_state=IDLE`을
제공했습니다. 현재 file-backed
`.pipeline/runs/20260520T061527Z-p65317/status.json`도
`active_round.state=VERIFYING`, `turn_state.state=IDLE`, `automation_health=ok`,
`automation_next_action=continue`를 보여주며 `automation_health_source`가 없습니다.
lane-local `status --json`, `doctor --json`, `tmux` 명령은 실행하지 않았습니다.

이번 source guard는 supervisor self-restart source set 안의 omission을 닫았습니다.
남은 같은 family의 가장 작은 local risk는 `pipeline_runtime/cli.py`의
`_RUNTIME_RELOAD_SOURCE_NAMES`가 아직 `pipeline_runtime/automation_health.py`를
포함하지 않는 점입니다. `pipeline_runtime/supervisor.py`는 CLI reload source list에
이미 포함돼 있지만, automation health helper 변경만으로는
`_runtime_source_newer_than_supervisor_pidfile()`이 supervisor reload 필요성을
감지한다는 regression이 없습니다. 따라서 다음 slice는 CLI/runtime reload source
list에 automation health helper를 포함시키는 bounded guard가 적절합니다.

operator-only 경계는 확인되지 않았습니다. publication, merge, credential/auth,
destructive action, approval-record repair, truth-sync repair, immediate safety
stop은 없고, advisory도 disabled이므로 `.pipeline/implement_handoff.md`로
수렴합니다.

## 사용 skill

- `round-handoff`: 최신 `/work` closeout을 code/test/runtime file evidence와
  대조하고 좁은 검증을 재실행하기 위해 사용했습니다.
- `next-slice-triage`: 검증 후 남은 same-family runtime reload source-list gap을
  operator/advisory가 아니라 하나의 local implement slice로 좁히기 위해
  사용했습니다.

## 확인한 대상

- `AGENTS.md`
- `.pipeline/harness/verify.md`
- `.pipeline/harness/council.md`
- `work/5/20/2026-05-20-supervisor-self-reload-source-guard.md`
- `verify/5/20/2026-05-20-automation-health-watcher-source-reload-guard.md`
- `.agents/skills/round-handoff/SKILL.md`
- `.agents/skills/next-slice-triage/SKILL.md`
- `.pipeline/runs/20260520T061527Z-p65317/status.json`
- `.pipeline/runs/20260520T061527Z-p65317/events.jsonl`
- `.pipeline/experimental.pid`
- `.pipeline/supervisor.pid`
- `pipeline_runtime/supervisor.py`
- `pipeline_runtime/automation_health.py`
- `pipeline_runtime/cli.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_pipeline_runtime_cli.py`

## 실행한 검증

- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_watcher_source_change_restarts_watcher_without_operator_decision tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_source_change_marks_watcher_restart_source tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_automation_health_source_change_marks_watcher_restart_source`
  - 결과: PASS. `Ran 3 tests in 0.013s`, `OK`.
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py work/5/20/2026-05-20-supervisor-self-reload-source-guard.md`
  - 결과: PASS. 출력 없음.
- `rg -n '"run_id"|"runtime_state"|"active_control_seq"|"automation_health"|"automation_next_action"|"automation_reason_code"|"automation_health_source"|"active_round"|"turn_state"|"state"' .pipeline/runs/20260520T061527Z-p65317/status.json`
  - 결과: CHECK. file-backed status에 `automation_health_source`는 없고,
    `active_round.state=VERIFYING`, `turn_state.state=IDLE`,
    `automation_health=ok`, `automation_next_action=continue`를 확인했습니다.
- `rg -n 'watcher_self_restart|watcher_source_updated|TASK_DONE|latest_work|automation_health_source|automation_health"|"automation_next_action' .pipeline/runs/20260520T061527Z-p65317/events.jsonl | tail -80`
  - 결과: CHECK. latest work `TASK_DONE`은 보였지만 `watcher_self_restart_*`
    이벤트는 확인되지 않았습니다.
- `stat -c '%n %Y %y' .pipeline/experimental.pid .pipeline/supervisor.pid pipeline_runtime/supervisor.py pipeline_runtime/automation_health.py pipeline_runtime/cli.py`
  - 결과: CHECK. `pipeline_runtime/supervisor.py`와
    `pipeline_runtime/automation_health.py`가 모두 runtime pidfile보다 최신입니다.
- `rg -n "_RUNTIME_RELOAD_SOURCE_NAMES|_runtime_source_newer_than_supervisor_pidfile|test_runtime_source_newer_than_supervisor_pidfile_requests_reload|automation_health.py" pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: CHECK. watcher self-restart source set에는 `automation_health.py`가 있으나,
    CLI runtime reload source set에는 아직 없습니다.

## 실행하지 않은 검증

- Playwright/e2e, controller startup, full smoke, broad unit, long soak는 실행하지
  않았습니다.
- 이유: 이번 검증 대상은 runtime source reload guard의 Python helper/test 범위이며,
  browser-visible contract나 controller webServer를 바꾸지 않았습니다.
- lane-local `status --json`, `doctor --json`, `tmux` 명령은 실행하지 않았습니다.

## 변경 파일

- `verify/5/20/2026-05-20-supervisor-self-reload-source-guard.md`

## 판정

- latest `/work`의 supervisor self-reload source guard는 verified입니다.
- watcher self-restart source set은 이제 `pipeline_runtime/automation_health.py`와
  `pipeline_runtime/supervisor.py`를 모두 포함합니다.
- 하지만 current file-backed runtime surface는 여전히 stale `ok/continue`를
  보여주고, CLI/runtime reload source list에는 `pipeline_runtime/automation_health.py`
  누락이 남아 있습니다.
- `.pipeline/advisory_request.md`는 `ADVISORY_ENABLED=false`라 쓰지 않습니다.
- `.pipeline/operator_request.md`를 새로 쓸 operator-only 경계는 없습니다.

## 다음 control 판정

COUNCIL_DECISION: implement
REASON_CODE: cli_runtime_reload_automation_health_source_guard
OWNER_ROLE: implement
NEXT_CONTROL_FILE: .pipeline/implement_handoff.md
NEXT_CONTROL_SEQ: 2006
EVIDENCE:
- `work/5/20/2026-05-20-supervisor-self-reload-source-guard.md`
- `verify/5/20/2026-05-20-supervisor-self-reload-source-guard.md`
- `pipeline_runtime/automation_health.py` mtime is newer than `.pipeline/supervisor.pid`
- `_WATCHER_SELF_RESTART_SOURCE_NAMES` includes `pipeline_runtime/automation_health.py`
- `_RUNTIME_RELOAD_SOURCE_NAMES` does not include `pipeline_runtime/automation_health.py`
REJECTED:
- `operator_required`: real operator-only boundary가 아니라 local source reload
  guard omission입니다.
- `advisory_followup`: `ADVISORY_ENABLED=false`입니다.
- `status_resample_only`: 같은 family의 stale status resample loop를 반복합니다.
- `live_restart`: 이번 control surface는 source guard 보강이며, live watcher/runtime
  restart는 handoff 범위로 넘기지 않습니다.
- `commit/push/PR publish`: implement lane 금지 사항이며 publication remains held입니다.

## 남은 리스크

- running watcher를 직접 재시작하지 않았으므로 current file-backed status는 이번
  verify 시점에도 새 provenance field를 쓰지 않습니다.
- 다음 implement slice는 live restart가 아니라 CLI/runtime reload source list가
  `pipeline_runtime/automation_health.py` 변경을 감지하는지 unit-level guard로
  검증해야 합니다.
- publication remains held. commit, push, branch/PR publication,
  PR creation/reuse/update, merge, release, external publication은 수행하지 않았습니다.
