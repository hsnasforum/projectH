# 2026-04-24 runtime launcher completed handoff preflight

## 변경 파일
- `pipeline_runtime/schema.py`
- `pipeline_runtime/supervisor.py`
- `watcher_core.py`
- `pipeline_runtime/cli.py`
- `pipeline_gui/backend.py`
- `pipeline-launcher.py`
- `tests/test_pipeline_runtime_schema.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_runtime_cli.py`
- `tests/test_pipeline_launcher.py`
- `tests/test_pipeline_gui_backend.py`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `work/4/24/2026-04-24-runtime-launcher-completed-handoff-preflight.md`

## 사용 skill
- `security-gate`: runtime start/stop, shell execution, control-slot handling 변경 범위를 local pipeline surface로 제한했습니다.
- `doc-sync`: launcher/supervisor/watcher 동작 변경을 현재 문서 truth에 맞춰 좁게 반영했습니다.
- `finalize-lite`: 변경 파일, 실제 검증, 문서 동기화, closeout 준비 상태를 함께 점검했습니다.
- `work-log-closeout`: 이번 구현 라운드의 파일, 검증, 남은 리스크를 `/work` closeout으로 기록했습니다.

## 변경 이유
- live status가 이미 검증 완료된 `CONTROL_SEQ: 104` `implement_handoff.md`를 canonical active control로 계속 보면서 자동화가 stale implement 표면에 묶일 수 있었습니다.
- start 경로는 `doctor`가 이미 갖고 있던 required launch checks를 spawn 전에 공통으로 사용하지 않아, profile/asset/CLI 누락을 GUI/TUI/CLI에서 같은 방식으로 막지 못했습니다.
- stop 경로는 graceful flush가 timeout된 뒤 강제 cleanup이 실제로 성공해도 `1`을 반환해, cleanup 성공을 실패로 보고하는 false negative가 있었습니다.

## 핵심 변경
- `schema.py`에 `referenced_work_paths_from_text()`와 `completed_implement_handoff_truth()`를 추가해 handoff가 참조한 `/work`와 `STATUS: verified` `/verify` 매칭을 공유 truth로 판정하게 했습니다.
- supervisor는 verified truth로 완료된 `STATUS: implement` handoff를 기존 duplicate handoff처럼 canonical `control=none`으로 내리고, `control_duplicate_ignored` event에 `work_path` / `verify_path` evidence를 남깁니다.
- watcher는 같은 shared truth를 사용해 완료된 handoff를 implement owner에게 재전달하지 않고 verify follow-up으로 되돌려 next-control cleanup을 이어가게 했습니다.
- CLI/GUI/TUI start 경로는 shared doctor preflight failure message를 확인한 뒤 required check 실패 시 spawn 전에 차단합니다.
- stop은 force kill 후 supervisor exit와 orphan/status cleanup이 끝나면 성공으로 반환하고, 실제로 supervisor가 남아 있을 때만 실패를 유지합니다.

## 검증
- `python3 -m unittest tests.test_pipeline_runtime_schema tests.test_pipeline_runtime_cli tests.test_pipeline_launcher tests.test_pipeline_gui_backend`
  - 통과: `Ran 159 tests ... OK`
- `python3 -m unittest tests.test_watcher_core.TurnResolutionTest tests.test_watcher_core.RollingSignalTransitionTest tests.test_watcher_core.ClaudeHandoffDispatchTest tests.test_pipeline_runtime_supervisor`
  - 통과: `Ran 195 tests ... OK`
- `git diff --check -- pipeline-launcher.py pipeline_gui/backend.py pipeline_runtime/cli.py pipeline_runtime/schema.py pipeline_runtime/supervisor.py watcher_core.py tests/test_pipeline_gui_backend.py tests/test_pipeline_launcher.py tests/test_pipeline_runtime_cli.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py README.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md`
  - 통과: 출력 없음
- `python3 -m pipeline_runtime.cli start . --mode experimental --session aip-projectH --no-attach`
  - 통과: live supervisor source reload/start 경로가 exit 0으로 완료됐습니다.
- `python3 -m pipeline_runtime.cli status . --json`
  - 통과: live runtime `RUNNING`, canonical `control.active_control_status = none`, `automation_health = ok`, `automation_next_action = continue`를 확인했습니다. 오래된 `implement_handoff.md`는 debug `compat.control_slots`에만 남습니다.
- `python3 -m pipeline_runtime.cli doctor . --json`
  - 통과: `ok = true`, required fail 0, warn 0을 확인했습니다.

## 남은 리스크
- full `python3 -m unittest discover -s tests -p 'test_*.py'`와 full browser/e2e suite는 이번 launcher-runtime slice 범위를 넘어서 실행하지 않았습니다.
- long soak는 돌리지 않았습니다. 대신 실제 local supervisor reload/start와 live status/doctor로 현재 런처 경로의 안정 상태를 확인했습니다.
- `compat.control_slots`에는 historical/debug 목적상 오래된 `implement_handoff.md`가 계속 보입니다. 자동화 판단은 canonical `control=none`과 watcher verify follow-up route를 사용합니다.
