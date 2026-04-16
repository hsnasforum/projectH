# 2026-04-16 runtime stale quiescent fastpath hardening

## 변경 파일
- `pipeline_gui/backend.py`
- `tests/test_pipeline_gui_backend.py`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/16/2026-04-16-runtime-stale-quiescent-fastpath-hardening.md`

## 사용 skill
- `security-gate`: runtime stop/read 경계 변경이 local-first read-model 범위를 벗어나지 않는지 점검했습니다.
- `doc-sync`: stale fast-path 동작을 runtime 문서에 현재 구현 truth로 반영했습니다.
- `work-log-closeout`: 실제 변경/검증/남은 리스크를 `/work` 형식으로 정리했습니다.

## 변경 이유
- 이전 라운드에서 graceful stop flush는 복구했지만, supervisor가 `finally`까지 못 가는 비정상 종료에서는 reader safety net 의존이 남아 있었습니다.
- 기존 `read_runtime_status()` 는 recent status 를 15초 동안 그대로 살려 두기 때문에, supervisor 가 이미 사라졌고 watcher/lane pid 도 다 죽은 상태에서 잠깐 `RUNNING` 또는 `DEGRADED` 착시가 남을 수 있었습니다.

## 핵심 변경
- `pipeline_gui/backend.py`
  - status payload 안의 watcher/lane pid 와 state 를 보고 실제 worker footprint 가 이미 quiescent 인지 판별하는 helper 를 추가했습니다.
  - recent status 라도 `runtime_state in {RUNNING, DEGRADED}` 이고 supervisor pid 가 없으며 watcher/lane pid 가 모두 quiescent 면 stale timeout 을 기다리지 않고 즉시 `BROKEN(supervisor_missing)` 으로 정규화하도록 보강했습니다.
  - `STARTING` 이나 pid 정보가 불완전한 recent status 는 기존처럼 보수적으로 유지해 start false alarm 을 피했습니다.
- `tests/test_pipeline_gui_backend.py`
  - recent `RUNNING` snapshot 이더라도 supervisor/watcher/lane pid 가 모두 dead 면 즉시 `BROKEN` 으로 정규화되는 회귀 테스트를 추가했습니다.
  - 기존 recent-status 보수 유지 테스트는 그대로 통과하는지 확인했습니다.
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`, `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - quiescent worker footprint 가 확인되면 reader 가 stale timeout 전에도 즉시 `BROKEN(supervisor_missing)` 으로 강등할 수 있다는 현재 동작을 문서에 반영했습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_gui_backend`
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`

## 남은 리스크
- 이 fast-path 는 watcher/lane pid 가 status 안에 남아 있을 때만 즉시 발동합니다. pid 정보가 비어 있는 recent snapshot 은 여전히 stale timeout safety net 에 의존합니다.
- `BROKEN` raw status 자체의 inactive field 정리는 controller UI 가 이미 가드하고 있어 급한 문제는 아니지만, API payload 의미를 더 엄격히 맞추려면 후속 라운드에서 별도 정리가 가능합니다.
- 이번 라운드는 reader hardening 범위만 다뤘고, `controller/index.html` 대규모 Office View diff 자체의 dead code/compat surface 추가 점검은 별도 slice 로 남습니다.
