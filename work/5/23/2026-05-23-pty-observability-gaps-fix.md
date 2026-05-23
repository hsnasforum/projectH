# 2026-05-23 PTY observability gaps fix

## 변경 파일
- `.pipeline/README.md`
- `pipeline_runtime/supervisor.py`
- `watcher_core.py`
- `watcher_pty_adapter.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- `tests/test_watcher_pty_adapter.py`
- `work/5/23/2026-05-23-pty-observability-gaps-fix.md`

## 사용 skill
- `security-gate`: runtime event와 status payload가 바뀌므로 local-first 로그/상태 노출, approval 경계, rollback 범위를 확인했습니다.
- `doc-sync`: PTY pilot event/status 계약이 바뀌어 `.pipeline/README.md`의 런타임 관찰 계약을 구현과 맞췄습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 검증, 남은 리스크를 이 closeout에 기록했습니다.

## 변경 이유
- live Gemini PTY smoke에서 `pty_pilot_lane_register`가 `raw.jsonl`에만 남고 current run `events.jsonl`에는 보이지 않는 관찰성 gap이 확인됐습니다.
- Gemini PTY child의 `alive`, `pid`, `exit_code` health가 lane status에 노출되지 않아 `status.json`만으로 PTY 상태를 확인하기 어려웠습니다.
- 이번 변경은 Gemini-only PTY pilot 관찰성 보강이며, Codex/Claude lane과 기존 tmux fallback 동작은 유지합니다.

## 핵심 변경
- `watcher_core.py`는 `_setup_pty_pilot_bridge()`에서 기존 `_log_raw()` 기록을 유지하고, `result=registered|failed`, `command`, `pty` health를 포함한 register payload를 deferred runtime event로 저장합니다.
- watcher exporter가 켜진 standalone 경로에서는 `_poll()` 첫 runtime tick에서 `pty_pilot_lane_register`를 current run `events.jsonl`에 한 번만 emit합니다.
- supervisor production writer 경로에서는 `pipeline_runtime/supervisor.py`가 current run 이후의 watcher raw `pty_pilot_lane_register`를 한 번만 mirror해 `events.jsonl`에 남깁니다.
- raw log tail이 밀려도 같은 watcher raw register 이벤트가 중복 mirror되지 않도록 supervisor mirror key를 payload 기반으로 고정했습니다.
- `watcher_pty_adapter.py`의 `PtyLaneBridge`에 `is_registered()`와 `health()`를 추가해 target별 PTY child health를 조회합니다.
- `status.json` lane status에는 Gemini PTY pilot health만 additive `pty: {alive, pid, exit_code}`로 붙이고, Codex/Claude status shape은 바꾸지 않습니다.
- `watcher_core.py`는 SIGTERM/SIGINT를 graceful shutdown으로 처리해 PTY bridge `teardown()`이 실행되도록 했습니다.
- `.pipeline/README.md`에 raw/event mirror와 Gemini-only `pty` status 계약을 문서화했습니다.

## 검증
- 통과: `python3 -m py_compile watcher_core.py watcher_pty_adapter.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_watcher_pty_adapter.py tests/test_pipeline_runtime_supervisor.py`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_watcher_raw_pty_pilot_event_is_mirrored_and_surfaces_lane_health tests.test_watcher_core.PtyPilotWiringTest tests.test_watcher_pty_adapter -v`
  - 결과: 14 tests OK
- 통과: `python3 -m unittest tests.test_watcher_core tests.test_watcher_pty_adapter tests.test_watcher_status_writer tests.test_watcher_lane_status -v`
  - 결과: 286 tests OK
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_supervisor tests.test_watcher_core tests.test_watcher_status_writer tests.test_watcher_lane_status tests.test_watcher_recovery tests.test_watcher_pty_adapter 2>&1 | tail -5`
  - 결과: 574 tests OK
- 통과: `git diff --check -- watcher_core.py watcher_pty_adapter.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_watcher_pty_adapter.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
- 통과: live re-smoke run `20260523T033000Z-p92980`
  - `events.jsonl`: `pty_pilot_lane_register` 1회, `payload.result=registered`, `payload.pty={alive:true,pid:93707,exit_code:null}`
  - `status.json`: Gemini lane에 `pty: {alive:true,pid:93707,exit_code:null}` 노출
  - 직전 patched run의 Gemini PTY pid `91883`/child `91910`은 재시작 후 종료 확인
  - watcher log에서 `ERROR`, `Traceback`, `Exception` 없음

## 남은 리스크
- `pty` health는 Gemini PTY pilot 등록 payload에서 온 child 상태입니다. 이후 child가 장시간 뒤 종료되는 상황의 지속 갱신은 별도 health telemetry 확장 후보입니다.
- live re-smoke는 operator wait 상태에서 수행되어 새 Codex implement / Claude verify dispatch cycle은 실행되지 않았습니다. 다만 Codex lane은 READY, watcher는 alive, profile adoption은 current를 유지했습니다.
- live 중복 관찰 전에 시작된 오래된 Gemini PTY 프로세스들이 남아 있을 수 있습니다. 이번 변경은 patched watcher 이후의 graceful shutdown을 검증했으며, 기존 orphan process cleanup은 별도 operator 승인 범위입니다.
- 선행 live smoke에서 남아 있던 `.pipeline/config/runtime_policy.json`, `verify/5/23/2026-05-23-live-gemini-pty-smoke.md`, `report/gemini/2026-05-23-pty-smoke-post-restart-verify.md`, `verify/5/23/2026-05-23-pty-gemini-wiring-pilot.md` 상태는 이번 범위에서 직접 정리하지 않았습니다.
- commit, push, PR, merge, release는 실행하지 않았습니다.
