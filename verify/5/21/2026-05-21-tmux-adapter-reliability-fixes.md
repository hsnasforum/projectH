# verify: 2026-05-21 tmux_adapter reliability fixes (A1/A2/B1/B2)

## 대상 work
`work/5/21/2026-05-21-tmux-adapter-reliability-fixes.md`

## 검증 결과: READY

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `py_compile` tmux_adapter / supervisor | PASS |
| `unittest` test_tmux_adapter 10개 + supervisor 215개 = 225개 | PASS (1.525s) |
| `git diff --check` | PASS |

## 코드 확인

| 항목 | 위치 | 확인 |
|---|---|---|
| A1: `TimeoutExpired` → `CompletedProcess(returncode=1)` | tmux_adapter.py:25 | ✓ |
| A2: `create_scaffold()` 실패 시 `kill_session()` 롤백 | tmux_adapter.py:83 | ✓ |
| B1: `get_pane_map()` / `cache_pane_map()` / `clear_pane_map_cache()` | tmux_adapter.py:219–235 | ✓ |
| B1: supervisor `_build_lane_statuses()`에서 1회 snapshot | supervisor.py:1699–1701 | ✓ |
| B2: `kill_lane()` → `respawn-pane -k "exec bash"` (pane 레이아웃 보존) | tmux_adapter.py:~151 | ✓ |
| B2: `restart_lane()` → `kill_lane()` + `spawn_lane()` | tmux_adapter.py: | ✓ |

## 설계 주목 사항

`kill_lane()`이 `kill-pane` 대신 `respawn-pane -k "exec bash"`를 사용합니다.
pane 레이아웃을 보존하면서 프로세스만 종료하는 접근이며,
기존 pane index 기반 주소 체계가 유지됩니다. 올바른 설계입니다.
