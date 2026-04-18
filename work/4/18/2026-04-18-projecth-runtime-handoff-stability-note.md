# 2026-04-18 projectH runtime handoff stability note

## 변경 파일
- `watcher_dispatch.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `pipeline_runtime/supervisor.py`
- `work/4/18/2026-04-18-projecth-runtime-handoff-stability-note.md`

## 사용 skill
- `doc-sync`: runtime handoff/drop 계약을 현재 구현 truth에 맞게 문서와 주석에 고정했습니다.
- `work-log-closeout`: 이번 라운드를 `/work` 형식에 맞춰 projectH 관점으로 정리했습니다.

## 변경 이유
- projectH 본프로젝트 작업 흐름에서 Claude/Codex/Gemini handoff가 꼬이면 실제 제품 구현 라운드가 멈추거나 잘못된 follow-up이 붙는 문제가 있었습니다.
- 이번 round의 직접 원인은 watcher pending queue가 active control을 한 번만 읽고 재사용해, 새 handoff가 열린 뒤에도 예전 control 기준으로 pending prompt를 drop/paste할 수 있었던 점이었습니다.
- owner-death / start-up race 보강은 이미 들어와 있었으므로, 이번 라운드는 그 위에 또 다른 heuristics를 얹지 않고 dispatch queue owner 경계를 바로잡는 데 집중했습니다.

## 핵심 변경
- `watcher_dispatch.py`의 `flush_pending()`이 pending 항목마다 active control을 다시 읽도록 바꿨습니다. 이제 최신 `CONTROL_SEQ`와 control file 기준으로 각 pending을 재판정합니다.
- pending drop 이유를 raw `control_mismatch` 한 종류로 뭉개지 않고 `control_seq_drift`, `control_file_drift`, `control_status_drift`, `active_control_missing`으로 나눴습니다.
- drop 시 raw log뿐 아니라 runtime event에도 `reason_code`, expected/active control seq, expected/active prompt path를 같이 남겨, 다음 재발 때 증상을 바로 분류할 수 있게 했습니다.
- `tests/test_watcher_core.py`에 queue 단위 회귀를 추가하고, stale operator pending이 새 Claude handoff 앞에서 structured reason과 함께 drop되는지 기존 통합 테스트를 강화했습니다.
- `pipeline_runtime/supervisor.py`와 `.pipeline/README.md`에는 `SIGKILL` stale pid cleanup responsibility가 supervisor `finally`가 아니라 watcher owner-death 경계에 있다는 현재 truth를 짧게 고정했습니다.

## 검증
- `python3 -m py_compile watcher_dispatch.py watcher_core.py pipeline_runtime/supervisor.py tests/test_watcher_core.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest`
  - 결과: `Ran 2 tests`, `OK`
- `python3 -m unittest -v tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_codex_pending_notification_is_dropped_before_claude_handoff_dispatch`
  - 결과: `Ran 1 test`, `OK`
- `python3 -m unittest -v tests.test_watcher_core`
  - 결과: `Ran 121 tests`, `OK`
- `git diff --check -- watcher_dispatch.py pipeline_runtime/supervisor.py tests/test_watcher_core.py .pipeline/README.md work/4/18/2026-04-18-projecth-runtime-handoff-stability-note.md`
  - 결과: 통과

## 남은 리스크
- 이번 라운드는 projectH 본프로젝트 작업 연속성을 가리는 watcher dispatch drift를 줄인 것이고, live tmux stability gate까지는 아직 포함하지 않았습니다.
- `SIGKILL` 뒤 stale `supervisor.pid` 파일 자체를 startup 시 옮기거나 정리하는 migration은 이번 범위 밖입니다.
- Claude idle timeout 오판, verify 중 artifact hash aliasing 같은 다른 incident family는 그대로 남아 있으므로, 재발 시 새 `reason_code`를 먼저 보고 다음 슬라이스를 고르는 편이 맞습니다.
