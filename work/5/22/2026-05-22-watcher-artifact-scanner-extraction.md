# 2026-05-22 watcher artifact scanner extraction

## 변경 파일
- `watcher_artifact_scanner.py`
- `watcher_core.py`
- `tests/test_watcher_artifact_scanner.py`
- `work/5/22/2026-05-22-watcher-artifact-scanner-extraction.md`

## 사용 skill
- `finalize-lite`: 실행한 검증, 미실행 범위, 문서 동기화 필요 여부, `/work` closeout 필요 여부를 정리하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- `watcher_core.py`에 work/verify markdown 스캔, metadata-only work note 판정, matching verify lookup, verify feedback/receipt state 계산이 남아 있어 core state machine 책임과 파일 스캔 책임이 섞여 있었습니다.
- A3 Step 4 범위는 advisory recovery나 turn state machine 분리는 보류하고, watch/verify artifact 스캔 로직만 독립 모듈로 분리하는 것이었습니다.

## 핵심 변경
- `watcher_artifact_scanner.py`를 추가해 `ArtifactScanner` dataclass를 만들었습니다.
- `ArtifactScanner`는 `watch_dir`, `verify_dir`, `repo_root`, `completion_paths`를 주입받아 기존 work/verify scan 동작을 수행합니다.
- `pipeline_runtime/schema.py`의 `is_canonical_round_note()`, `latest_verify_note_for_work()`, `same_day_verify_dir_for_work()`, `normalize_repo_artifact_path()`를 재사용했습니다.
- `watcher_core.py`는 `self._scanner`를 초기화하고 `_is_dispatchable_work_note()`, `_get_work_tree_snapshot()`, `_work_has_matching_verify()`, `_get_latest_verify_candidate_path()` 등 기존 scanner 성격 메서드를 위임으로 교체했습니다.
- `verified_work_paths`와 `completion_paths`처럼 WatcherCore에 남아 있던 실제 의존성은 wrapper에서 주입해 기존 동작을 보존했습니다.
- `tests/test_watcher_artifact_scanner.py`를 추가해 metadata-only 필터링, same-day/cross-day verify reference matching, latest candidate 정책, verify feedback/receipt state를 독립 검증했습니다.

## 검증
- 통과: `python3 -m py_compile watcher_core.py watcher_artifact_scanner.py tests/test_watcher_artifact_scanner.py`
  - 결과: PASS, 출력 없음.
- 통과: `python3 -m py_compile watcher_core.py watcher_artifact_scanner.py`
  - 결과: PASS, 출력 없음.
- 통과: `python3 -m unittest tests.test_watcher_artifact_scanner -v`
  - 결과: `Ran 4 tests in 0.036s`, `OK`.
- 통과: `python3 -m unittest tests.test_watcher_core -v 2>&1 | tail -5`
  - 결과: `Ran 264 tests in 10.425s`, `OK`.
- 통과: `python3 -c "from watcher_artifact_scanner import ArtifactScanner; print('import OK')"`
  - 결과: `import OK`.
- 통과: `git diff --check -- watcher_core.py watcher_artifact_scanner.py`
  - 결과: PASS, 출력 없음.
- 통과: `git diff --check -- watcher_core.py watcher_artifact_scanner.py tests/test_watcher_artifact_scanner.py`
  - 결과: PASS, 출력 없음.

## 남은 리스크
- 이번 slice는 work/verify artifact scan 로직의 위치를 바꾸는 내부 리팩터링입니다. live watcher/tmux runtime 검증은 실행하지 않았습니다.
- `watcher_core.py`는 이전 helper extraction, control signal extraction, job state extraction 변경이 이미 남아 있는 dirty 파일입니다. 이번 slice에서는 ArtifactScanner 초기화와 scanner 성격 메서드 위임부만 추가로 변경했습니다.
- `latest_round_markdown()`은 날짜 우선 정렬과 반환 형식이 기존 WatcherCore 스캔 동작과 달라 재사용하지 않았습니다.
- product docs, agent/skill config, `.pipeline` control slot은 변경하지 않았습니다.
- commit, push, branch/PR publication, PR creation, merge, release, publication은 실행하지 않았습니다.
