# 2026-05-23 pty gemini wiring pilot

## 변경 파일
- `watcher_pty_adapter.py`
- `watcher_core.py`
- `.pipeline/config/runtime_policy.json`
- `.pipeline/README.md`
- `tests/test_watcher_pty_adapter.py`
- `tests/test_watcher_core.py`
- `work/5/23/2026-05-23-pty-gemini-wiring-pilot.md`

## 사용 skill
- `security-gate`: PTY subprocess shell execution이 기본 비활성, local-first, Gemini-only pilot, tmux fallback 유지인지 점검했습니다.
- `doc-sync`: 새 `runtime_policy.json` 플래그와 현재 동작을 `.pipeline/README.md`에 좁게 반영했습니다.
- `finalize-lite`: 실행한 검증과 미실행 live smoke 범위, 남은 리스크를 정리했습니다.
- `work-log-closeout`: 실제 변경 파일과 검증 결과를 이 `/work` closeout으로 기록했습니다.

## 변경 이유
- Step 10 wiring 계획에 따라 Step 9의 `PtyAdapter` pilot을 바로 critical implement/verify 경로에 연결하지 않고, 현재 profile에서 비활성 physical lane인 Gemini target에만 조건부로 연결해야 했습니다.
- `runtime_policy.json`의 `pty_pilot_lane` 기본값은 `""`로 두어 shipped runtime 기본 동작을 tmux 기반으로 유지하고, `"Gemini"`으로 명시한 경우에만 PTY pilot을 활성화하도록 했습니다.
- bridge가 `None`을 반환하거나 비활성인 경우 기존 tmux capture/send 경로로 fallback하도록 해 실패 반경을 줄였습니다.

## 핵심 변경
- `watcher_pty_adapter.py`에 `PtyLaneBridge`를 추가했습니다. `pane_target -> PtyLane` 매핑과 `register`, `capture`, `send`, `teardown`을 제공하며, 미등록/비활성 lane은 `None`으로 fallback 신호를 반환합니다.
- `watcher_core.py`가 `load_runtime_policy()`로 `pty_pilot_lane`을 읽고, 값이 `"Gemini"`이고 dry-run이 아닐 때만 Gemini pane target을 `PtyLaneBridge`에 등록합니다.
- `watcher_core.py`의 capture/send 경로는 helper를 통해 Gemini target만 PTY bridge를 먼저 시도하고, Codex/Claude target과 bridge fallback은 기존 tmux capture/send를 사용합니다.
- `WatcherCore.run()` 종료 시 `PtyLaneBridge.teardown()`을 호출해 pilot child lane을 정리하도록 했습니다.
- `.pipeline/config/runtime_policy.json`에 기본 비활성 `pty_pilot_lane: ""`을 추가하고, `.pipeline/README.md`에 Gemini-only PTY pilot과 fallback 계약을 기록했습니다.
- 테스트는 `PtyLaneBridge` fallback 계약과 `WatcherCore` runtime-policy wiring이 Gemini target에만 적용되고 Codex/Claude path는 tmux로 유지되는지 검증합니다.

## 검증
- 통과: `python3 -m json.tool .pipeline/config/runtime_policy.json`
- 통과: `python3 -m py_compile watcher_core.py watcher_pty_adapter.py tests/test_watcher_core.py tests/test_watcher_pty_adapter.py`
- 통과: `python3 -m unittest -v tests.test_watcher_pty_adapter tests.test_watcher_core.PtyPilotWiringTest`
  - 결과: 10 tests OK
- 통과: `python3 -m unittest tests.test_watcher_pty_adapter tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_supervisor tests.test_watcher_core tests.test_watcher_status_writer tests.test_watcher_lane_status tests.test_watcher_recovery 2>&1 | tail -5`
  - 결과: 570 tests OK
- 통과: `git diff --check -- watcher_core.py watcher_pty_adapter.py tests/test_watcher_core.py tests/test_watcher_pty_adapter.py .pipeline/config/runtime_policy.json .pipeline/README.md work/5/23/2026-05-23-pty-gemini-wiring-pilot.md`

## 남은 리스크
- live Gemini PTY smoke는 실행하지 않았습니다. 실제 `gemini --yolo` 장시간 child, 터미널 크기, attach/debug UX, backpressure는 후속 live pilot에서 확인해야 합니다.
- 기본값은 `pty_pilot_lane: ""`라 현재 shipped runtime은 계속 tmux 기반입니다. `"Gemini"` 활성화는 별도 operator/runtime 설정 변경이 필요합니다.
- `tmux_send_escape` 기반 advisory cancel은 이번 slice에서 PTY로 우회하지 않았습니다. 이번 범위는 capture/send prompt 경로의 Gemini-only pilot입니다.
- commit, push, PR, merge, release는 실행하지 않았습니다. `PUBLISH_HELD` 경계는 유지됩니다.
