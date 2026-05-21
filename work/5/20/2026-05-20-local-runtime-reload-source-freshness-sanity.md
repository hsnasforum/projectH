# 2026-05-20 local runtime reload source freshness sanity

## 변경 파일

- `.pipeline/current_run.json` (runtime command가 갱신)
- `.pipeline/supervisor.pid` (runtime command가 갱신)
- `.pipeline/runs/20260520T061527Z-p65317/status.json` (runtime command 이후 갱신)
- `.pipeline/runs/20260520T061527Z-p65317/events.jsonl` (runtime command 이후 갱신)
- `.pipeline/runs/20260520T072614Z-p2/status.json` (runtime command가 생성)
- `.pipeline/runs/20260520T072614Z-p2/events.jsonl` (runtime command가 생성)
- `work/5/20/2026-05-20-local-runtime-reload-source-freshness-sanity.md`

## 사용 skill

- `work-log-closeout`: local runtime reload sanity 결과, file-backed runtime evidence, 실행한 체크, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#2007`이 이전 소스 freshness guard 변경을 실제 file-backed runtime surface가 로드할 수 있도록 local reload sanity를 한 번 실행하라고 지시했습니다.
- 이전 verify는 `pipeline_runtime/automation_health.py`, `pipeline_runtime/supervisor.py`, `pipeline_runtime/cli.py`가 `.pipeline/supervisor.pid`보다 최신인 상태를 확인했습니다.
- 이번 라운드는 소스 수정이 아니라 `pipeline_runtime.cli start --no-attach` local reload boundary 실행과 file-backed evidence 기록만 범위로 삼았습니다.

## 핵심 변경

- `python3 -m pipeline_runtime.cli start /home/xpdlqj/code/projectH --mode experimental --no-attach`를 정확히 한 번 실행했습니다.
- 명령 자체는 exit code 0으로 종료했고 stdout/stderr 출력은 없었습니다.
- reload 명령 이후 새 run 디렉터리 `.pipeline/runs/20260520T072614Z-p2`가 생성됐고 `.pipeline/supervisor.pid`가 `2026-05-20 16:26:14 +0900`로 갱신됐습니다.
- 새 run `20260520T072614Z-p2`의 `status.json`은 `runtime_state=BROKEN`, `automation_health=needs_operator`, `automation_reason_code=runtime_launch_failed:RuntimeError`, `automation_next_action=operator_required`를 기록했습니다.
- 새 run에는 `automation_health_source`가 포함됐고 `derived_by=pipeline_runtime.automation_health.derive_automation_health`, `ruleset_version=2026-05-20.active_verify_round_status_v1`, `runtime_state=BROKEN`, `turn_state=IMPLEMENT_ACTIVE`, `next_action=operator_required`로 기록됐습니다.
- `.pipeline/current_run.json`은 최종적으로 기존 run `20260520T061527Z-p65317`을 계속 가리켰고, 해당 status는 `runtime_state=STARTING`, `automation_health=recovering`, `automation_reason_code=runtime_starting`, `automation_next_action=retrying`, `watcher.alive=false`였습니다.
- handoff가 금지한 lane-local `status --json`, `doctor --json`, `tmux` 명령은 실행하지 않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA `0bea63787a4e04c5c728505403df4c7d8fb24ffc1e3a22275beb1b4cc7744e15`와 일치했습니다.
- `python3 -m pipeline_runtime.cli start /home/xpdlqj/code/projectH --mode experimental --no-attach`
  - 결과: exit code 0. 출력 없음.
- `sed -n '1,220p' .pipeline/current_run.json`
  - 결과: `run_id=20260520T061527Z-p65317`, `watcher_pid=0`, `updated_at=2026-05-20T07:26:58.614603Z`.
- `rg -n '"run_id"|"runtime_state"|"automation_health"|"automation_next_action"|"automation_health_source"|"active_round"|"turn_state"|"active_control_seq"' .pipeline/runs/20260520T061527Z-p65317/status.json`
  - 결과: 기존 current run은 `runtime_state=STARTING`, `active_control_seq=2007`, `active_round=null`, `turn_state=IMPLEMENT_ACTIVE`, `automation_health=recovering`, `automation_next_action=retrying`.
- `rg -n '"run_id"|"runtime_state"|"automation_health"|"automation_next_action"|"automation_health_source"|"active_round"|"turn_state"|"active_control_seq"' .pipeline/runs/20260520T072614Z-p2/status.json`
  - 결과: 새 run은 `runtime_state=BROKEN`, `automation_health=needs_operator`, `automation_next_action=operator_required`, `automation_health_source` 포함.
- `tail -80 .pipeline/runs/20260520T072614Z-p2/events.jsonl`
  - 결과: `runtime_started` 뒤 `automation_incident`가 `runtime_launch_failed:RuntimeError` / `operator_required`로 기록됐습니다.
- `stat -c '%n %Y %y' .pipeline/supervisor.pid .pipeline/experimental.pid pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py pipeline_runtime/cli.py`
  - 결과: `.pipeline/supervisor.pid`는 갱신됐고 `.pipeline/experimental.pid`는 존재하지 않아 `stat`가 해당 경로에서 실패했습니다. source 파일들은 여전히 supervisor pid보다 과거 mtime입니다.
- `git diff --check -- work/5/20/2026-05-20-local-runtime-reload-source-freshness-sanity.md`
  - 결과: PASS.
- `git diff --check --no-index -- /dev/null work/5/20/2026-05-20-local-runtime-reload-source-freshness-sanity.md`
  - 결과: PASS. diff 존재로 exit code는 1이지만 whitespace error 출력은 없었습니다.

## 남은 리스크

- reload 명령은 exit code 0이었지만 새 run `20260520T072614Z-p2`는 내부 runtime surface에서 `BROKEN` / `runtime_launch_failed:RuntimeError`를 기록했습니다.
- `.pipeline/current_run.json`은 새 run으로 유지되지 않고 기존 run `20260520T061527Z-p65317`을 가리켰습니다. 기존 run은 stale `VERIFYING + IDLE + ok/continue` 조합에서는 벗어났지만 `STARTING + recovering + retrying` 상태이며 `watcher.alive=false`입니다.
- 새 run에는 `automation_health_source`가 포함됐지만, 현재 포인터가 가리키는 기존 run status에는 `automation_health_source`가 아직 없습니다.
- `.pipeline/experimental.pid`는 reload 이후 존재하지 않았습니다.
- 이번 라운드는 handoff 범위상 소스 수정, broad unit/e2e, controller Playwright/webServer/full-smoke, commit, push, branch/PR publication, merge, release를 수행하지 않았습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았습니다.
