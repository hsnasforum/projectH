# verify: 2026-05-22 watcher_control_signals extraction (A3 Step 2)

## 검증 결과: READY — 268개 통과

| 검사 | 결과 |
|---|---|
| `py_compile` watcher_core + watcher_control_signals | PASS |
| `unittest` test_watcher_control_signals 4개 + test_watcher_core 264개 | PASS |
| import smoke | OK |
| `git diff --check` | PASS |

## 코드 확인

| 항목 | 위치 | 확인 |
|---|---|---|
| `ControlSignalReader` dataclass | watcher_control_signals.py:1 | ✓ |
| `newest_control_signal`, `control_signal_matches`, `control_signal_for_slot` | watcher_control_signals.py | ✓ |
| `self._csreader` 초기화 | watcher_core.py:412 | ✓ |
| `_control_signal_reader()` 프로퍼티 (advisory/operator 갱신) | watcher_core.py:1316–1319 | ✓ |
| `_get_path_sig` 캐시 WatcherCore 유지, `path_sig_fn`으로 주입 | watcher_core.py | ✓ |

## watcher_core.py 줄 수 추이

| 슬라이스 | 줄 수 | 감소 |
|---|---|---|
| 원본 | 4498 | — |
| Step 1 (모듈 함수 이동) | 4430 | −68 |
| Step 2 (제어 신호 추출) | 4385 | −45 |
| **누계** | **4385** | **−113** |

## 다음 단계 (A3 Step 3)

Job state 관리 메서드 추출 → `watcher_job_state.py`
대상: `_get_current_run_jobs`, `_archive_job_state_file`,
`_archive_stale_job_states`, `_archive_current_run_job`,
`_archive_matching_verified_pending_jobs`
