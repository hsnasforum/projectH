# 2026-05-22 verify_fsm export boundary

## 변경 파일
- `verify_fsm.py`
- `tests/test_verify_fsm.py`
- `work/5/22/2026-05-22-verify-fsm-export-boundary.md`

## 사용 skill
- `finalize-lite`: 실행한 검증, 미실행 범위, 문서 동기화 필요 여부, `/work` closeout 필요 여부를 정리하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- 2121에서 `JobState`, `JobStatus`, `TERMINAL_STATES` 정의를 `watcher_state.py`로 옮긴 뒤에도 `verify_fsm.py` 상단의 import가 내부 사용인지 하위 호환 re-export인지 코드만으로 구분하기 어려웠습니다.
- 이번 slice는 `verify_fsm.py`가 직접 소유하는 API와 `watcher_state`에서 다시 내보내는 호환 API를 명시해 후속 정리의 기준선을 세우는 것이었습니다.

## 핵심 변경
- `verify_fsm.py`에 `__all__`을 추가해 `StateMachine`, `make_job_id`, file signature 함수 3개를 직접 소유 API로 표시했습니다.
- `JobState`, `JobStatus`, `TERMINAL_STATES`는 `watcher_state`에서 온 backward-compatible re-export로 `__all__`에 분리해 표시했습니다.
- re-export import 블록 위에 새 코드는 `watcher_state`에서 직접 import해야 한다는 주석을 추가했습니다.
- `SCHEMA_VERSION`은 persisted `JobState` payload 호환용 내부 alias로만 남기고 `__all__`에서는 제외했습니다.
- `tests/test_verify_fsm.py`에 export boundary smoke test를 추가해 `JobState` re-export와 `StateMachine`, `compute_file_sig` import가 계속 동작하는지 검증했습니다.

## 검증
- 확인: `grep -rn "from verify_fsm import" . --include="*.py" | grep -v "test_\|__pycache__"`
  - 결과: 생산 코드에서는 `watcher_core.py`가 `StateMachine`, `compute_file_sig`, `make_job_id`를 import하고, `watcher_artifact_scanner.py`가 file signature 함수 3개를 import합니다.
- 확인: `grep -n "SCHEMA_VERSION" verify_fsm.py`
  - 결과: `SCHEMA_VERSION`은 `JOB_STATE_SCHEMA_VERSION` alias 정의 위치 외 사용 없음.
- 통과: `python3 -m py_compile verify_fsm.py`
  - 결과: PASS, 출력 없음.
- 통과: `python3 -c "import verify_fsm; assert hasattr(verify_fsm, '__all__'), 'no __all__'; from verify_fsm import JobState, StateMachine, compute_file_sig; print('export boundary OK')"`
  - 결과: `export boundary OK`.
- 통과: `python3 -m unittest tests.test_verify_fsm tests.test_watcher_core -v 2>&1 | tail -5`
  - 결과: `Ran 275 tests in 9.204s`, `OK`.
- 통과: `git diff --check -- verify_fsm.py`
  - 결과: PASS, 출력 없음.
- 추가 통과: `git diff --check -- verify_fsm.py tests/test_verify_fsm.py`
  - 결과: PASS, 출력 없음.

## 남은 리스크
- 이번 slice는 export boundary 주석과 `__all__`, import smoke test만 추가했습니다. `verify_fsm.py` 내부 state machine 로직은 변경하지 않았습니다.
- `compute_file_sig`, `compute_md_tree_sig`, `compute_multi_file_sig`, `make_job_id`, `StateMachine`의 소유 위치는 그대로 `verify_fsm.py`에 남겼습니다.
- live watcher/tmux runtime 검증은 실행하지 않았습니다.
- product docs, agent/skill config, `.pipeline` control slot은 변경하지 않았습니다.
- commit, push, branch/PR publication, PR creation, merge, release, publication은 실행하지 않았습니다.
