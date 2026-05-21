# verify: 2026-05-22 watcher_job_state extraction (A3 Step 3)

## 검증 결과: READY — 268개 통과

| 검사 | 결과 |
|---|---|
| `py_compile` watcher_core / watcher_job_state | PASS |
| `unittest` test_watcher_job_state 4개 + test_watcher_core 264개 | PASS |
| import smoke | OK |
| `git diff --check` | PASS |

## watcher_core.py 줄 수 추이

| 슬라이스 | 줄 수 | 감소 |
|---|---|---|
| 원본 | 4498 | — |
| Step 1 (모듈 함수 이동) | 4430 | −68 |
| Step 2 (ControlSignalReader) | 4385 | −45 |
| Step 3 (JobStateManager) | 4323 | −62 |
| **누계** | **4323** | **−175** |

## 추출된 모듈

| 파일 | 줄 수 | 책임 |
|---|---|---|
| watcher_control_signals.py | 122 | ControlSignalReader, 제어 신호 파싱 |
| watcher_job_state.py | 126 | JobStateManager, job state 관리 |

## 주목할 발견

JobState, JobStatus, TERMINAL_STATES가 watcher_state.py가 아닌
verify_fsm.py에 정의되어 있음. 향후 타입 정의 위치 통합 후보.

## 다음 후보 (A3 Step 4)

Advisory recovery 메서드 추출 → watcher_advisory.py
대상: _stale_advisory_recovery_marker, _recover_stale_advisory,
_retry_advisory_if_idle, _supersede_advisory_request_for_recovery 등
