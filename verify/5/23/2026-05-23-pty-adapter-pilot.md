# verify: 2026-05-23 PtyAdapter pilot (2158)

## 대상 work
`work/5/23/2026-05-23-pty-adapter-pilot.md`

## 검증 결과: READY

---

## 코드 확인

| 항목 | 위치 | 확인 |
|---|---|---|
| `PtyLane` — spawn/send/capture/kill/health | `watcher_pty_adapter.py` | ✓ |
| `PtyAdapter` — TmuxAdapter 호환 인터페이스 7개 메서드 | `watcher_pty_adapter.py` | ✓ |
| 배경 reader thread + deque(maxlen=200) 버퍼 | `watcher_pty_adapter.py` | ✓ |
| 기존 소스 파일 변경 없음 (watcher_core, TmuxAdapter, cli, supervisor) | — | ✓ |

## 회귀 검증

| 검사 | 결과 |
|---|---|
| `python3 -m py_compile` | PASS |
| `tests.test_watcher_pty_adapter` 7개 | **PASS** |
| 전체 회귀 suite 560개 | **PASS (0 FAIL, 0 ERROR)** |
| `git diff --check` | PASS |

## 테스트 커버리지

| 테스트 | 검증 내용 |
|---|---|
| `test_spawn_lane_starts_subprocess_and_marks_alive` | spawn 후 is_alive=True |
| `test_capture_tail_returns_subprocess_output` | deque 버퍼에서 출력 반환 |
| `test_send_input_writes_bytes_to_master_fd` | master_fd에 bytes 쓰기 |
| `test_kill_lane_terminates_subprocess_and_marks_not_alive` | kill 후 is_alive=False |
| `test_restart_lane_kills_and_respawns` | kill → spawn 순서 |
| `test_session_exists_returns_true_when_any_lane_is_alive` | 활성 lane 존재 여부 |
| `test_missing_lane_health_returns_expected_keys` | 미존재 lane health dict 형태 |

---

## A3 Step 9 위치

| 항목 | 수치 |
|---|---|
| `watcher_pty_adapter.py` | 236줄 (격리 파일럿) |
| 추가 테스트 | 7개 |
| 기존 560개 suite | 변화 없음 |
| watcher_core.py | 3858줄 (변경 없음) |

격리 파일럿 완료. Step 10 (wiring 결정)은 별도 operator 결정 필요.
