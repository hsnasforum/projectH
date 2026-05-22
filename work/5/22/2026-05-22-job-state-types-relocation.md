# 2026-05-22 job state types relocation

## 변경 파일
- `watcher_state.py`
- `verify_fsm.py`
- `watcher_job_state.py`
- `watcher_artifact_scanner.py`
- `watcher_core.py`
- `work/5/22/2026-05-22-job-state-types-relocation.md`

## 사용 skill
- `finalize-lite`: 실행한 검증, 미실행 범위, 문서 동기화 필요 여부, `/work` closeout 필요 여부를 정리하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- `JobState`, `JobStatus`, `TERMINAL_STATES`는 watcher runtime 상태 타입이지만 역사적으로 `verify_fsm.py`에 정의되어 있어 타입 위치와 책임이 어긋나 있었습니다.
- A3 후속 추출에서 `watcher_job_state.py`, `watcher_artifact_scanner.py`, `watcher_core.py`가 watcher 상태 타입을 직접 참조하므로, 타입 소유 위치를 `watcher_state.py`로 옮기고 `verify_fsm.py`는 하위 호환 re-export를 유지하는 것이 이번 범위였습니다.

## 핵심 변경
- `watcher_state.py`에 `JobStatus`, `TERMINAL_STATES`, `JobState` 정의를 추가했습니다.
- `JobState.save()`와 `JobState.load()`의 기존 primary/fallback job state 파일 동작은 그대로 옮겼고, job state 로그는 기존 `watcher_core` logger 이름을 유지했습니다.
- `verify_fsm.py`에서는 기존 타입 정의를 제거하고 `watcher_state`에서 `JobState`, `JobStatus`, `TERMINAL_STATES`를 re-export하도록 변경했습니다.
- `verify_fsm.SCHEMA_VERSION` 호환을 위해 `watcher_state.JOB_STATE_SCHEMA_VERSION` alias를 유지했습니다.
- `watcher_job_state.py`, `watcher_artifact_scanner.py`, `watcher_core.py`의 직접 타입 import를 `watcher_state` 경로로 업데이트했습니다.
- `compute_file_sig`, `compute_md_tree_sig`, `compute_multi_file_sig`, `StateMachine`, `make_job_id`는 이번 범위 밖이므로 `verify_fsm.py`에 그대로 남겼습니다.

## 검증
- 통과: `python3 -m py_compile watcher_state.py verify_fsm.py watcher_job_state.py watcher_artifact_scanner.py watcher_core.py`
  - 결과: PASS, 출력 없음.
- 통과: `python3 -m unittest tests.test_watcher_core tests.test_watcher_job_state tests.test_watcher_artifact_scanner -v 2>&1 | tail -5`
  - 결과: `Ran 272 tests in 9.723s`, `OK`.
- 통과: `python3 -c "from watcher_state import JobState, JobStatus, TERMINAL_STATES; from verify_fsm import JobState as JobState2; assert JobState is JobState2, 're-export mismatch'; print('타입 이전 OK, 하위 호환 OK')"`
  - 결과: `타입 이전 OK, 하위 호환 OK`.
- 통과: `git diff --check -- watcher_state.py verify_fsm.py`
  - 결과: PASS, 출력 없음.
- 추가 통과: `python3 -m unittest tests.test_verify_fsm -v 2>&1 | tail -5`
  - 결과: `Ran 10 tests in 0.045s`, `OK`.
- 추가 통과: `git diff --check -- watcher_state.py verify_fsm.py watcher_job_state.py watcher_artifact_scanner.py watcher_core.py`
  - 결과: PASS, 출력 없음.

## 남은 리스크
- 이번 slice는 타입 정의 위치와 import 경로만 변경했습니다. live watcher/tmux runtime 검증은 실행하지 않았습니다.
- 테스트 파일의 `from verify_fsm import JobState` 형태는 하위 호환 re-export 검증을 겸하므로 유지했습니다.
- product docs, agent/skill config, `.pipeline` control slot은 변경하지 않았습니다.
- commit, push, branch/PR publication, PR creation, merge, release, publication은 실행하지 않았습니다.
