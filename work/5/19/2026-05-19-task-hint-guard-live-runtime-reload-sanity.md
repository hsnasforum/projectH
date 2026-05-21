# 2026-05-19 task hint guard live runtime reload sanity

## 변경 파일

- `work/5/19/2026-05-19-task-hint-guard-live-runtime-reload-sanity.md`
- `.pipeline/current_run.json` (runtime-managed, gitignored)
- `.pipeline/runs/20260519T150559Z-p337092/status.json` (runtime-managed, gitignored)
- `.pipeline/runs/20260519T150559Z-p337092/events.jsonl` (runtime-managed, gitignored)
- `.pipeline/runs/20260519T150559Z-p337092/task-hints/codex.json` (runtime-managed, gitignored)
- `.pipeline/compat/**` (runtime-managed, gitignored)

## 사용 skill

- `security-gate`: runtime start, local process/status surface, runtime-managed logs/artifacts 경계가 local-first이며 publication/외부 작업으로 확장되지 않았는지 확인하기 위해 사용했습니다.
- `work-log-closeout`: handoff #1982 실행 결과, 실제 검증, 환경 hold, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1982`가 검증된 `pipeline_runtime/supervisor.py` task-hint identity guard를 live local runtime에 source-aware start boundary로 반영하고, runtime surface를 기록하라고 지시했습니다.
- 이전 검증의 남은 리스크는 live runtime이 새 `supervisor.py` 코드를 로드했다고 아직 주장할 수 없다는 점이었습니다.

## 핵심 변경

- `sha256sum .pipeline/implement_handoff.md`로 handoff SHA가 요청값 `37fc6dd0101bdd6ddd7d3213afa944726c80ed68c52c2b0e34d6d7ca73e1cc87`와 일치함을 확인했습니다.
- `python3 -m pipeline_runtime.cli start . --mode experimental --no-attach`를 한 번 실행했습니다. 명령은 exit code 0, 출력 없음으로 종료됐습니다.
- 후속 `status --json`은 run id `20260519T150559Z-p337092`, active control `.pipeline/implement_handoff.md#1982 implement`, Codex lane `READY`, active round `null`을 보였지만, runtime은 `STARTING`, `automation_health=recovering`, `automation_reason_code=runtime_starting`, `automation_next_action=retrying`, watcher `alive=false`에 머물렀습니다.
- 따라서 live runtime reload 성공 또는 release/full-smoke readiness는 주장하지 않고 `local_runtime_reload_env_held`로 기록합니다.
- `.pipeline/runs/20260519T150559Z-p337092/task-hints/codex.json`은 `job_id=ctrl-1982`, `dispatch_id=seq-1982`, `control_seq=1982`를 보여 stale closed verify round identity가 implement task-hint로 노출되지 않는 표면은 확인했습니다.
- handoff의 필수 unittest 명령에 포함된 `test_supervisor_restart_inherits_run_id_when_watcher_is_alive_so_status_follows_verify_replay`는 현재 테스트 클래스에 존재하지 않아 실패했습니다. `rg`로 실제 테스트명이 `test_supervisor_inherits_run_id_when_watcher_is_alive_so_status_follows_verify_replay`임을 확인했고, 같은 의도의 실제 테스트로 보정 실행했습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA와 일치했습니다.
- `python3 -m pipeline_runtime.cli start . --mode experimental --no-attach`
  - 결과: PASS(exit code 0), 출력 없음.
- `python3 -m pipeline_runtime.cli status . --json`
  - 결과: PARTIAL / ENV HELD. `ok=true`이나 `runtime_state=STARTING`, `automation_health=recovering`, `automation_next_action=retrying`, watcher `alive=false`였습니다.
- `python3 -m py_compile pipeline_runtime/cli.py pipeline_runtime/supervisor.py`
  - 결과: PASS, 출력 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_task_hints_implement_lane_ignores_closed_verify_round_identity tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_restart_inherits_run_id_when_watcher_is_alive_so_status_follows_verify_replay`
  - 결과: FAIL. 첫 번째 테스트는 통과했으나 두 번째 테스트명은 `AttributeError`로 존재하지 않았습니다.
- `rg -n "inherits_run_id|status_follows_verify_replay|watcher_is_alive" tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS. 실제 테스트명 `test_supervisor_inherits_run_id_when_watcher_is_alive_so_status_follows_verify_replay`를 확인했습니다.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_task_hints_implement_lane_ignores_closed_verify_round_identity tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_inherits_run_id_when_watcher_is_alive_so_status_follows_verify_replay`
  - 결과: PASS. 2개 테스트 통과.
- `sed -n '1,120p' .pipeline/runs/20260519T150559Z-p337092/task-hints/codex.json`
  - 결과: PASS. `job_id=ctrl-1982`, `dispatch_id=seq-1982`, `control_seq=1982` 확인.
- `ps -p 7 -o pid=,ppid=,stat=,args= || true`
  - 결과: 출력 없음. sandbox process namespace에서는 pidfile 값 `7`을 live supervisor process로 확인하지 못했습니다.
- `ps -eo pid=,ppid=,stat=,args= | rg "pipeline_runtime\.cli|RuntimeSupervisor|tmux new-session|codex" | head -40`
  - 결과: host runtime supervisor 대신 sandbox command process만 보였습니다. 이 증거로 operator stop을 작성하지 않았습니다.
- `git diff --check -- work/5/19/2026-05-19-task-hint-guard-live-runtime-reload-sanity.md`
  - 결과: PASS, 출력 없음.

## 남은 리스크

- `local_runtime_reload_env_held`: source-aware start 명령은 성공했지만 runtime status가 `STARTING/retrying`에 머물러 live supervisor가 새 code로 안정화됐다고 주장할 수 없습니다.
- watcher는 status surface에서 `alive=false`였습니다. 다만 handoff 지시상 lane-local runtime/process evidence만으로 `.pipeline/operator_request.md`를 작성하지 않았습니다.
- handoff의 required unittest 이름 하나가 repo 현재 테스트명과 불일치했습니다. 실제 테스트명으로 보정 실행한 결과는 PASS였지만, 원문 required command 자체는 FAIL로 기록했습니다.
- 제품 코드, runtime code, tests, docs, Playwright selector, browser UI, storage schema는 수정하지 않았습니다.
- Playwright, `make e2e-test`, controller startup, long soak는 실행하지 않았고 release-ready, publication-ready, full-smoke-pass, merge-ready 상태를 주장하지 않습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았습니다.
- commit, push, branch/PR publication, PR creation/reuse/update, merge, release, external publication은 수행하지 않았습니다.
