# 2026-04-21 launch-side runtime reload

## 변경 파일
- `pipeline_runtime/cli.py`
- `tests/test_pipeline_runtime_cli.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/21/2026-04-21-launch-side-runtime-reload.md`

## 사용 skill
- `security-gate`: live supervisor stop/start와 background runtime 재기동이 local-first runtime 경계 안에 머무르는지 확인했습니다.
- `doc-sync`: launch-side reload 계약을 `.pipeline/README.md`와 runtime 기술/운영 문서에 반영했습니다.
- `work-log-closeout`: 실행한 명령, 실제 runtime 재시작 결과, 남은 리스크를 표준 `/work` 형식으로 남깁니다.

## 변경 이유
- 직전 라운드의 watcher self-restart는 새 supervisor 코드가 이미 실행 중일 때는 동작하지만, old supervisor가 계속 떠 있으면 새 self-restart 코드를 import하지 못하는 빈틈이 있었습니다.
- `pipeline_runtime.cli start`가 live supervisor를 발견하면 그대로 no-op 하던 경로 때문에, launcher Start만으로는 old supervisor를 새 코드로 교체하지 못할 수 있었습니다.
- 이번 라운드는 그 빈틈을 launch-side에서 닫고, 실제 현재 runtime도 새 run으로 재시작했습니다.

## 핵심 변경
- `pipeline_runtime/cli.py`에 runtime reload source 목록과 `.pipeline/supervisor.pid` mtime 비교 helper를 추가했습니다.
- `_spawn_supervisor()`는 live daemon이 있어도 runtime source가 pidfile보다 새로우면 `_stop_supervisor()`로 graceful stop 후 새 daemon을 띄웁니다.
- source가 더 새롭지 않으면 기존처럼 live daemon을 재사용해 불필요한 restart를 피합니다.
- 문서에는 old supervisor가 새 watcher self-restart 코드를 import하지 못한 상태도 다음 Start/Restart 경계에서 operator 결정 없이 닫힌다고 명시했습니다.
- 실제 `python3 -m pipeline_runtime.cli restart /home/xpdlqj/code/projectH --mode experimental --no-attach`를 실행해 current run을 새 코드로 재기동했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/cli.py pipeline_runtime/supervisor.py pipeline_runtime/lane_surface.py watcher_core.py`
  - 출력 없음, `rc=0`
- `python3 -m unittest tests.test_pipeline_runtime_cli.SupervisorCliTest.test_runtime_source_newer_than_supervisor_pidfile_requests_reload tests.test_pipeline_runtime_cli.SupervisorCliTest.test_spawn_supervisor_replaces_live_daemon_when_runtime_source_changed tests.test_pipeline_runtime_cli.SupervisorCliTest.test_spawn_supervisor_keeps_live_daemon_when_runtime_source_is_not_newer`
  - `Ran 3 tests`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_cli`
  - `Ran 21 tests`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - `Ran 120 tests`, `OK`
- `python3 -m unittest tests.test_pipeline_launcher`
  - `Ran 24 tests`, `OK`
- `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 출력 없음, `rc=0`
- `python3 -m pipeline_runtime.cli restart /home/xpdlqj/code/projectH --mode experimental --no-attach`
  - `rc=0`
  - current run: `20260421T091515Z-p361782`
  - supervisor pid: `361784`
  - watcher pid: `362087`
  - status: `runtime_state=RUNNING`, `watcher.alive=true`, `automation_health=ok`, `automation_next_action=continue`

## 남은 리스크
- launch-side reload는 Start/Restart 경계에서 old supervisor를 교체합니다. 아무 CLI/launcher action도 없는 상태에서 이미 실행 중인 old supervisor를 외부에서 즉시 갈아끼우는 별도 daemon은 두지 않았습니다.
- runtime은 현재 새 코드로 실행 중이며, active control은 기존 `.pipeline/gemini_request.md` `CONTROL_SEQ=656`을 이어받아 advisory lane이 작업 중입니다.
