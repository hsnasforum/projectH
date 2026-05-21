STATUS: verified_with_supervisor_self_reload_gap
WORK: work/5/20/2026-05-20-automation-health-watcher-source-reload-guard.md
PREVIOUS_VERIFY: verify/5/20/2026-05-20-active-verify-round-runtime-source-provenance.md
CONTROL_SEQ_NEXT: 2005
ADVISORY_ENABLED: false

# 검증 기록

## 요약

`work/5/20/2026-05-20-automation-health-watcher-source-reload-guard.md`의
핵심 주장은 검증됐습니다. `_WATCHER_SELF_RESTART_SOURCE_NAMES`에는
`pipeline_runtime/automation_health.py`가 추가됐고, 새 regression은
automation health helper가 `experimental.pid`보다 최신이면
`_watcher_source_restart_marker()`의 `source_path`가 해당 helper를 가리킴을
확인합니다.

다만 file-backed runtime surface는 아직 current source truth를 반영하지
못합니다. `RUNTIME_STATUS_AT_DISPATCH`는 `RUNNING + ok/continue`와
`active_round=VERIFY_PENDING`, `turn_state=IDLE`을 dispatcher authority로
제공했고, 현재 `.pipeline/runs/20260520T061527Z-p65317/status.json`도
`active_round.state=VERIFYING`, `turn_state.state=IDLE`, `automation_health=ok`,
`automation_next_action=continue`를 보여주며 `automation_health_source`가 없습니다.
이는 lane-local runtime command 증거가 아니라 file-backed status surface
확인입니다.

추가 파일 근거상 `.pipeline/experimental.pid`의 mtime은
`2026-05-20 15:15:27 +0900`이고, `pipeline_runtime/supervisor.py`의 mtime은
`2026-05-20 16:09:47 +0900`입니다. 그러나 같은 run의 `events.jsonl`에는
`watcher_self_restart_started` / `watcher_self_restart_completed` 이벤트가
없습니다. 직전 slice가 source list를 바꾼 파일 자체가
`pipeline_runtime/supervisor.py`였는데, `_WATCHER_SELF_RESTART_SOURCE_NAMES`는
현재도 supervisor 자체를 포함하지 않습니다. 따라서 다음 local slice는
automation health helper guard를 반복하지 말고, watcher self-restart source set이
`pipeline_runtime/supervisor.py` 자체 변경도 marker로 잡도록 하는 exact guard여야
합니다.

operator-only 경계는 확인되지 않았습니다. publication, merge, credential/auth,
destructive action, approval-record repair, truth-sync repair, immediate safety
stop은 없고, advisory도 disabled이므로 `.pipeline/implement_handoff.md`로
수렴합니다.

## 사용 skill

- `round-handoff`: 최신 `/work` closeout을 code/test/runtime file evidence와
  대조하고 좁은 검증을 재실행하기 위해 사용했습니다.
- `next-slice-triage`: 검증 후 남은 same-family source reload freshness risk를
  operator/advisory가 아니라 하나의 local implement slice로 좁히기 위해
  사용했습니다.

## 확인한 대상

- `AGENTS.md`
- `.pipeline/harness/verify.md`
- `.pipeline/harness/council.md`
- `work/5/20/2026-05-20-automation-health-watcher-source-reload-guard.md`
- `verify/5/20/2026-05-20-active-verify-round-runtime-source-provenance.md`
- `.agents/skills/round-handoff/SKILL.md`
- `.agents/skills/next-slice-triage/SKILL.md`
- `.pipeline/runs/20260520T061527Z-p65317/status.json`
- `.pipeline/runs/20260520T061527Z-p65317/events.jsonl`
- `.pipeline/experimental.pid`
- `pipeline_runtime/supervisor.py`
- `pipeline_runtime/automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `pipeline_runtime/cli.py`

## 실행한 검증

- `python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_automation_health.py`
  - 결과: PASS.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_watcher_source_change_restarts_watcher_without_operator_decision tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_automation_health_source_change_marks_watcher_restart_source`
  - 결과: PASS. `Ran 2 tests in 0.010s`, `OK`.
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py pipeline_runtime/automation_health.py tests/test_pipeline_runtime_automation_health.py work/5/20/2026-05-20-automation-health-watcher-source-reload-guard.md`
  - 결과: PASS. 출력 없음.
- `rg -n '"run_id"|"runtime_state"|"active_control_seq"|"automation_health"|"automation_next_action"|"automation_reason_code"|"automation_health_source"|"active_round"|"turn_state"|"state"|"source_path"|"watcher_self_restart"' .pipeline/runs/20260520T061527Z-p65317/status.json`
  - 결과: CHECK. file-backed status에 `automation_health_source`는 없고,
    `active_round.state=VERIFYING`, `turn_state.state=IDLE`,
    `automation_health=ok`, `automation_next_action=continue`를 확인했습니다.
- `tail -n 80 .pipeline/runs/20260520T061527Z-p65317/events.jsonl`
  - 결과: CHECK. latest work dispatch/accept/done 흐름은 보이지만
    `watcher_self_restart_*` 이벤트는 확인되지 않았습니다.
- `stat -c '%n %Y %y' .pipeline/experimental.pid pipeline_runtime/supervisor.py pipeline_runtime/automation_health.py`
  - 결과: CHECK. `pipeline_runtime/supervisor.py`와
    `pipeline_runtime/automation_health.py`가 모두 `experimental.pid`보다 최신입니다.
- `rg -n 'watcher_self_restart|watcher_source_updated|automation_health_source|automation_health"|"automation_next_action|active_round|turn_state' .pipeline/runs/20260520T061527Z-p65317/events.jsonl .pipeline/runs/20260520T061527Z-p65317/status.json`
  - 결과: CHECK. status stale surface와 historical automation incidents는 보였지만
    `watcher_self_restart_*` 이벤트는 없었습니다.
- `rg -n "def _maybe_restart_watcher_for_source_change|_maybe_restart_watcher_for_source_change\\(" pipeline_runtime/supervisor.py watcher_core.py`
  - 결과: CHECK. supervisor loop가 `_maybe_restart_watcher_for_source_change()`를
    호출하는 경로를 확인했습니다.
- `sed -n '60,120p' pipeline_gui/platform.py`,
  `rg -n "RUNTIME_RELOAD_SOURCE_NAMES|runtime_reload|source.*reload|watcher_source" pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py tests/test_watcher_core.py`
  - 결과: CHECK. CLI/runtime restart source list는 별도 reload boundary로 남아
    있지만, 이번 next slice의 가장 직접적인 evidence는 supervisor self-restart
    source set의 self-file omission입니다.

## 실행하지 않은 검증

- Playwright/e2e, controller startup, full smoke, broad unit, long soak는 실행하지
  않았습니다.
- 이유: 이번 검증 대상은 runtime source reload guard의 Python helper/test 범위이며,
  browser-visible contract나 controller webServer를 바꾸지 않았습니다.
- lane-local `status --json`, `doctor --json`, `tmux` 명령은 실행하지 않았습니다.

## 변경 파일

- `verify/5/20/2026-05-20-automation-health-watcher-source-reload-guard.md`

## 판정

- latest `/work`의 automation health watcher source reload guard는 verified입니다.
- `pipeline_runtime/automation_health.py` helper 변경은 source restart marker 대상에
  포함됐습니다.
- 하지만 live/file-backed runtime surface는 아직 stale입니다. supervisor source
  itself가 `experimental.pid`보다 최신인데도 self-restart event가 없고,
  `_WATCHER_SELF_RESTART_SOURCE_NAMES`가 `pipeline_runtime/supervisor.py` 자체를
  포함하지 않는 것이 확인됐습니다.
- `.pipeline/advisory_request.md`는 `ADVISORY_ENABLED=false`라 쓰지 않습니다.
- `.pipeline/operator_request.md`를 새로 쓸 operator-only 경계는 없습니다.

## 다음 control 판정

COUNCIL_DECISION: implement
REASON_CODE: supervisor_self_reload_source_guard
OWNER_ROLE: implement
NEXT_CONTROL_FILE: .pipeline/implement_handoff.md
NEXT_CONTROL_SEQ: 2005
EVIDENCE:
- `work/5/20/2026-05-20-automation-health-watcher-source-reload-guard.md`
- `verify/5/20/2026-05-20-automation-health-watcher-source-reload-guard.md`
- `pipeline_runtime/supervisor.py` mtime is newer than `.pipeline/experimental.pid`
- file-backed `events.jsonl` has no `watcher_self_restart_*` event
- `_WATCHER_SELF_RESTART_SOURCE_NAMES` includes `pipeline_runtime/automation_health.py`
  but not `pipeline_runtime/supervisor.py`
REJECTED:
- `operator_required`: real operator-only boundary가 아니라 local source reload
  guard omission입니다.
- `advisory_followup`: `ADVISORY_ENABLED=false`입니다.
- `status_resample_only`: 같은 family의 stale status resample loop를 반복합니다.
- `commit/push/PR publish`: implement lane 금지 사항이며 publication remains held입니다.

## 남은 리스크

- running watcher를 직접 재시작하지 않았으므로 current file-backed status는 이번
  verify 시점에도 새 provenance field를 쓰지 않습니다.
- 다음 implement slice는 live restart가 아니라
  `pipeline_runtime/supervisor.py` 자체 변경이 watcher self-restart marker/restart
  path에 포함되는지 unit-level guard로 검증해야 합니다.
- CLI/runtime reload source list에도 `pipeline_runtime/automation_health.py`가 없는
  별도 freshness gap이 관찰됐지만, 이번 next control은 더 직접적인 supervisor
  self-file omission에 먼저 한정합니다.
- publication remains held. commit, push, branch/PR publication,
  PR creation/reuse/update, merge, release, external publication은 수행하지 않았습니다.
