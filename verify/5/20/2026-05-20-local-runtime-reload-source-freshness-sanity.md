STATUS: verified_with_local_socket_launch_guard_gap
WORK: work/5/20/2026-05-20-local-runtime-reload-source-freshness-sanity.md
PREVIOUS_VERIFY: verify/5/20/2026-05-20-cli-runtime-reload-automation-health-source-guard.md
CONTROL_SEQ_NEXT: 2008
ADVISORY_ENABLED: false

# 검증 기록

## 요약

`work/5/20/2026-05-20-local-runtime-reload-source-freshness-sanity.md`의
핵심 기록은 현재 file-backed runtime evidence와 일치합니다. implement 라운드는
`python3 -m pipeline_runtime.cli start /home/xpdlqj/code/projectH --mode experimental --no-attach`
를 한 번 실행했고, 명령 자체는 exit code 0으로 끝났지만 새 run
`20260520T072614Z-p2`는 `runtime_state=BROKEN` 및
`automation_health=needs_operator`를 기록했습니다.

추가 확인 결과, 새 run의 `logs/launch-error.log`에는 실제 원인이
`error connecting to /tmp/tmux-1000/default (Operation not permitted)`로 남아
있습니다. 즉 새 run의 generic `runtime_launch_failed:RuntimeError` surface는
로컬 tmux socket 권한 거부를 세부 원인으로 갖고 있습니다.

`RUNTIME_STATUS_AT_DISPATCH`는 dispatcher authority로
`runtime_state=STARTING`, `automation_health=recovering`,
`automation_next_action=retrying`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`
을 제공했습니다. 따라서 새 run의 lane/local launch failure evidence만으로
`.pipeline/operator_request.md`를 새로 쓰지 않습니다. 이 라운드의 안전한 다음
조치는 operator stop이 아니라 local socket launch failure가
`operator_required`로 과분류되지 않도록 runtime health surface를 좁게 보강하는
same-family risk-reduction slice입니다.

## 사용 skill

- `round-handoff`: 최신 `/work` closeout을 현재 file-backed runtime evidence와
  대조하고 좁은 검증을 재실행하기 위해 사용했습니다.
- `next-slice-triage`: advisory disabled 상태에서 operator-only 경계와 local
  runtime surface 보강 후보를 비교해 하나의 implement slice로 좁히기 위해
  사용했습니다.

## 확인한 대상

- `AGENTS.md`
- `.pipeline/harness/verify.md`
- `.pipeline/harness/council.md`
- `work/5/20/2026-05-20-local-runtime-reload-source-freshness-sanity.md`
- `verify/5/20/2026-05-20-cli-runtime-reload-automation-health-source-guard.md`
- `.pipeline/implement_handoff.md`
- `.pipeline/current_run.json`
- `.pipeline/runs/20260520T061527Z-p65317/status.json`
- `.pipeline/runs/20260520T061527Z-p65317/events.jsonl`
- `.pipeline/runs/20260520T072614Z-p2/status.json`
- `.pipeline/runs/20260520T072614Z-p2/events.jsonl`
- `.pipeline/runs/20260520T072614Z-p2/logs/launch-error.log`
- `pipeline_runtime/supervisor.py`
- `pipeline_runtime/automation_health.py`
- `pipeline_runtime/tmux_adapter.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`

## 실행한 검증

- `git diff --check -- work/5/20/2026-05-20-local-runtime-reload-source-freshness-sanity.md`
  - 결과: PASS. 출력 없음.
- `git diff --check --no-index -- /dev/null work/5/20/2026-05-20-local-runtime-reload-source-freshness-sanity.md`
  - 결과: PASS. diff 존재로 exit code는 1이지만 whitespace error 출력은 없었습니다.
- `sed -n '1,220p' .pipeline/current_run.json`
  - 결과: current pointer는 `20260520T061527Z-p65317`를 가리키며 `watcher_pid=0`입니다.
- `rg -n '"run_id"|"runtime_state"|"automation_health"|"automation_reason_code"|"automation_next_action"|"automation_health_source"|"active_round"|"turn_state"|"active_control_seq"|"watcher"|"alive"' .pipeline/runs/20260520T061527Z-p65317/status.json`
  - 결과: current run은 `runtime_state=STARTING`, `active_round.state=VERIFYING`,
    `turn_state.state=IDLE`, `automation_health=recovering`,
    `automation_reason_code=runtime_starting`, `automation_next_action=retrying`,
    `watcher.alive=false`입니다. 이 status에는 `automation_health_source`가 없습니다.
- `rg -n '"run_id"|"runtime_state"|"degraded_reason"|"automation_health"|"automation_reason_code"|"automation_next_action"|"automation_health_source"|"active_round"|"turn_state"|"active_control_seq"|"watcher"|"alive"' .pipeline/runs/20260520T072614Z-p2/status.json`
  - 결과: 새 run은 `runtime_state=BROKEN`, `degraded_reason=runtime_launch_failed:RuntimeError`,
    `automation_health=needs_operator`, `automation_reason_code=runtime_launch_failed:RuntimeError`,
    `automation_next_action=operator_required`, `automation_health_source` 포함입니다.
- `tail -40 .pipeline/runs/20260520T072614Z-p2/events.jsonl`
  - 결과: `runtime_started` 뒤 `automation_incident`가
    `runtime_launch_failed:RuntimeError` / `operator_required`로 기록됐습니다.
- `wc -c .pipeline/runs/20260520T072614Z-p2/logs/launch-error.log && sed -n '1,20p' .pipeline/runs/20260520T072614Z-p2/logs/launch-error.log`
  - 결과: 68 bytes. 내용은
    `error connecting to /tmp/tmux-1000/default (Operation not permitted)`입니다.

## 실행하지 않은 검증

- `pipeline_runtime.cli start`는 이번 verify에서 다시 실행하지 않았습니다.
  - 이유: 직전 implement 라운드가 handoff 지시에 따라 이미 한 번 실행했고,
    이번 검증 목적은 그 결과 evidence를 대조하는 것입니다.
- lane-local `status --json`, `doctor --json`, `tmux` 명령은 실행하지 않았습니다.
  - 이유: active prompt가 해당 명령을 dispatcher surface와 충돌할 때 비권위
    evidence로 취급하라고 지시했습니다.
- Playwright/e2e, controller startup, full smoke, broad unit, long soak는 실행하지
  않았습니다.
  - 이유: 이번 검증 대상은 local runtime reload evidence와 runtime health surface
    판정이며 browser-visible contract를 바꾸지 않았습니다.

## 변경 파일

- `verify/5/20/2026-05-20-local-runtime-reload-source-freshness-sanity.md`

## 판정

- latest `/work`의 reload sanity 기록은 verified입니다.
- reload command는 exit code 0으로 끝났지만 새 run은 내부적으로 `BROKEN`을 기록했습니다.
- 새 run의 generic `runtime_launch_failed:RuntimeError`는 launch-error log 기준으로
  local tmux socket permission denial입니다.
- 현재 dispatcher authority와 current run surface는 `STARTING/recovering/retrying`이고,
  prompt rules는 lane-local tmux/socket access conflict만으로 operator stop을 쓰지 말라고
  지시합니다.
- advisory는 disabled이므로 `.pipeline/advisory_request.md`를 쓰지 않습니다.
- commit, push, branch/PR publication, PR creation/reuse/update, merge, release,
  external publication은 이번 verify 범위가 아닙니다.

## 다음 control 판정

COUNCIL_DECISION: implement
REASON_CODE: runtime_launch_socket_guard_surface
OWNER_ROLE: implement
NEXT_CONTROL_FILE: .pipeline/implement_handoff.md
NEXT_CONTROL_SEQ: 2008
EVIDENCE:
- `work/5/20/2026-05-20-local-runtime-reload-source-freshness-sanity.md`
- `.pipeline/runs/20260520T072614Z-p2/status.json`
- `.pipeline/runs/20260520T072614Z-p2/logs/launch-error.log`
- `RUNTIME_STATUS_AT_DISPATCH` reports `STARTING + recovering + retrying`
REJECTED:
- `operator_required`: local tmux socket permission denial from a launch attempt is
  not a publication, merge, credential/auth repair, destructive action,
  approval-record repair, truth-sync blocker, or immediate safety boundary in
  this prompt.
- `advisory_followup`: `ADVISORY_ENABLED=false`입니다.
- `rerun_runtime_start`: the previous implement already ran the local reload once,
  and repeating it would likely reproduce the same socket-held evidence without
  reducing future automation drift.
- `status_resample_only`: the next risk is the generic `RuntimeError` /
  `operator_required` surface for a known local socket-held condition.

## 남은 리스크

- current run status에는 아직 `automation_health_source`가 없고,
  `STARTING/recovering/retrying` 상태가 계속됩니다.
- 새 run에는 `automation_health_source`가 있지만, local socket permission denial이
  generic `runtime_launch_failed:RuntimeError` / `operator_required`로 표면화됐습니다.
- 다음 slice는 runtime launch failure detail을 보존하면서 local socket-held failure를
  canonical local guard reason으로 분류하는 focused code/test/doc 보강이어야 합니다.
