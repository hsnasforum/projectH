# 2026-05-22 watcher job state extraction

## 변경 파일
- `watcher_job_state.py`
- `watcher_core.py`
- `tests/test_watcher_job_state.py`
- `work/5/22/2026-05-22-watcher-job-state-extraction.md`

## 사용 skill
- `security-gate`: JobState archive가 실제 파일 이동을 수행하므로 archive 경계, 실패 시 기존 무시 동작, 로컬 state 보존을 확인하기 위해 사용했습니다.
- `finalize-lite`: 실행한 검증, 미실행 범위, 문서 동기화 필요 여부, `/work` closeout 필요 여부를 정리하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- `watcher_core.py`에 JobState archive, stale cleanup, current-run job 조회/보관 로직이 남아 있어 WatcherCore 본문 책임이 계속 커지고 있었습니다.
- A3 Step 3 범위는 의존성이 큰 `_archive_matching_verified_pending_jobs()`는 그대로 두고, 의존성이 낮은 4개 메서드만 독립 매니저로 추출하는 것이었습니다.

## 핵심 변경
- `watcher_job_state.py`를 추가해 `JobStateManager` dataclass를 만들었습니다.
- `JobStateManager`는 `state_dir`, `run_id`, `archive_dir_fn`, `started_at`, `state_cleanup_legacy_grace_sec`를 주입받아 기존 JobState archive/cleanup/read 동작을 수행합니다.
- `watcher_core.py`는 `self._jsm`을 초기화하고 `_archive_job_state_file()`, `_archive_stale_job_states()`, `_get_current_run_jobs()`, `_archive_current_run_job()`을 위임으로 교체했습니다.
- WatcherCore의 기존 메서드 시그니처는 유지했고, `_job_state_manager()`에서 mutable runtime 속성을 위임 전 동기화하도록 했습니다.
- `_archive_matching_verified_pending_jobs()`는 이번 범위 밖으로 유지했습니다.
- `tests/test_watcher_job_state.py`를 추가해 archive 파일 이동, stale job cleanup, current-run filter/sort, current-run archive를 독립 검증했습니다.

## 검증
- 통과: `python3 -m py_compile watcher_core.py watcher_job_state.py tests/test_watcher_job_state.py`
  - 결과: PASS, 출력 없음.
- 통과: `python3 -m py_compile watcher_core.py watcher_job_state.py`
  - 결과: PASS, 출력 없음.
- 통과: `python3 -m unittest tests.test_watcher_job_state -v`
  - 결과: `Ran 4 tests in 0.027s`, `OK`.
- 통과: `python3 -m unittest tests.test_watcher_core -v 2>&1 | tail -5`
  - 결과: `Ran 264 tests in 11.136s`, `OK`.
- 통과: `python3 -c "from watcher_job_state import JobStateManager; print('import OK')"`
  - 결과: `import OK`.
- 통과: `git diff --check -- watcher_core.py watcher_job_state.py`
  - 결과: PASS, 출력 없음.
- 통과: `git diff --check -- watcher_core.py watcher_job_state.py tests/test_watcher_job_state.py`
  - 결과: PASS, 출력 없음.

## 남은 리스크
- 이번 slice는 JobState 관리 로직의 위치를 바꾸는 내부 리팩터링입니다. live watcher/tmux runtime 검증은 실행하지 않았습니다.
- `watcher_core.py`는 이전 helper extraction 및 control signal extraction 변경이 이미 남아 있는 dirty 파일입니다. 이번 slice에서는 JobStateManager 초기화와 4개 job state 메서드 위임부만 추가로 변경했습니다.
- `_archive_matching_verified_pending_jobs()`는 의존성 과다로 이번 범위에서 제외했으며 기존 위치에 그대로 남겼습니다.
- product docs, agent/skill config, `.pipeline` control slot은 변경하지 않았습니다.
- commit, push, branch/PR publication, PR creation, merge, release, publication은 실행하지 않았습니다.
