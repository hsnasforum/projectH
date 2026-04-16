# 2026-04-16 controller graceful stop flush and contract audit

## 변경 파일
- `pipeline_runtime/cli.py`
- `pipeline_runtime/supervisor.py`
- `controller/index.html`
- `controller/server.py`
- `tests/test_pipeline_runtime_cli.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_controller_server.py`
- `README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/16/2026-04-16-controller-graceful-stop-flush-and-contract-audit.md`

## 사용 skill
- `doc-sync`: controller/runtime 계약 변경을 README와 runtime 문서에 현재 구현 truth로 맞췄습니다.
- `security-gate`: stop lifecycle와 controller runtime command surface가 여전히 local-first, bounded runtime control 범위 안에 있는지 점검했습니다.
- `work-log-closeout`: 이번 라운드의 실제 수정/검증/남은 리스크를 `/work` 형식으로 정리했습니다.

## 변경 이유
- stop 이후 watcher와 lane은 죽었는데 runtime이 `STOPPING`에 머물거나 stale control이 살아 보여 controller가 아직 active처럼 보이는 문제가 남아 있었습니다.
- 기존 reader normalization은 안전망으로는 유효했지만, stop 성공 기준이 supervisor final flush가 아니라는 점이 근본 리스크였습니다.
- `controller/index.html`은 canonical runtime 경로만 쓰는데 `controller/server.py`에는 legacy/unused route가 남아 있어 UI 계약과 서버 surface가 어긋나 있었습니다.

## 핵심 변경
- `pipeline_runtime/cli.py`
  - stop 경로를 `SIGTERM -> final STOPPED flush 대기 -> 필요 시에만 SIGKILL fallback` 순서로 바꿨습니다.
  - stop 성공 판단에 `runtime_state=STOPPED`, `control=none`, `active_round=null`, watcher dead, lane `OFF` flush 완료를 포함시켰습니다.
- `pipeline_runtime/supervisor.py`
  - `_write_status(force_runtime_state=...)` 경로를 추가해 supervisor `finally`에서 `STOPPING`, final `STOPPED`를 명시적으로 기록하도록 정리했습니다.
  - live control/round/lane 초기화는 일반 inactive status 전체가 아니라 final `STOPPED` flush에만 적용되도록 경계를 좁혔습니다.
- `controller/index.html`
  - log modal의 lane `Pause/Resume/Restart` affordance를 제거해 backend route 없는 버튼이 남지 않게 했습니다.
- `controller/server.py`
  - browser active contract에 없는 `/api/state`, `/api/health`, legacy `/api/start|stop|restart`, `/api/runtime/attach` route를 제거했습니다.
  - controller browser surface를 `/api/runtime/status`, `/api/runtime/start|stop|restart`, `/api/runtime/capture-tail`로 맞췄습니다.
- `tests/test_pipeline_runtime_cli.py`, `tests/test_pipeline_runtime_supervisor.py`, `tests/test_controller_server.py`
  - graceful stop flush, final `STOPPED` write, controller HTTP contract 축소를 각각 회귀 테스트로 고정했습니다.
- `README.md`, `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`, `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - graceful stop flush가 primary truth이고 reader normalization은 fallback safety net이라는 점, browser controller active contract가 축소되었다는 점을 문서에 반영했습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor`
- `python3 -m unittest -v tests.test_pipeline_runtime_cli tests.test_pipeline_gui_backend tests.test_controller_server`
- `python3 -m unittest -v tests.test_controller_server tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_supervisor tests.test_pipeline_gui_backend`
- `python3 -m py_compile controller/server.py pipeline_runtime/cli.py pipeline_runtime/supervisor.py`
- `git diff --check -- pipeline_runtime/cli.py pipeline_runtime/supervisor.py controller/index.html controller/server.py tests/test_pipeline_runtime_cli.py tests/test_pipeline_runtime_supervisor.py tests/test_controller_server.py README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- controller 실제 흐름 확인:
  - `kill 3401670`
  - `setsid env CONTROLLER_HOST=127.0.0.1 python3 -m controller.server >/tmp/projecth-controller.log 2>&1 < /dev/null &`
  - `curl -s http://127.0.0.1:8780/api/runtime/status`
  - `python3 - <<'PY' ... /api/runtime/start -> /api/runtime/status poll -> /api/runtime/stop -> /api/runtime/status poll ... PY`
  - 실제 결과 핵심:
    - start 직후 `runtime_state=RUNNING`, `control_status=implement`, `active_round.state=VERIFY_PENDING`, watcher alive 확인
    - stop 직후 첫 poll에서 `runtime_state=STOPPED`, `control_status=none`, `active_round=null`, watcher dead, lane state=`OFF` 확인

## 남은 리스크
- supervisor가 `finally`까지 도달하지 못하고 비정상 종료하면 reader의 stale normalization safety net은 여전히 필요합니다.
- `controller/index.html`은 현재 큰 Office View 개편 diff 안에 있으므로, 이번 라운드는 runtime/status 소비 경계와 modal action contract까지만 점검했습니다.
- controller browser surface에서는 attach를 제거했지만, 하위 runtime attach 기능 자체는 `pipeline_gui`/launcher 쪽에 남아 있으므로 이후 operator UX 재정의가 필요하면 별도 slice에서 다시 설계해야 합니다.
