# 2026-05-22 watcher runtime exporter extraction

## 변경 파일
- `watcher_runtime_exporter.py`
- `watcher_core.py`
- `tests/test_watcher_runtime_exporter.py`
- `work/5/22/2026-05-22-watcher-runtime-exporter-extraction.md`

## 사용 skill
- `security-gate`: `current_run.json`과 `events.jsonl` 기록 경계가 로컬 파일 기록으로 유지되고, 비활성화 시 쓰지 않는지 확인하기 위해 사용했습니다.
- `finalize-lite`: 실행한 검증, 미실행 범위, 문서 동기화 필요 여부, `/work` closeout 필요 여부를 정리하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- `watcher_core.py`에 runtime pointer 기록과 runtime event append 로직이 남아 있어 WatcherCore 본문 책임이 계속 커지고 있었습니다.
- A3 Step 5 범위는 turn state 의존이 큰 `_write_runtime_status()`는 보류하고, 독립 가능한 `_write_current_run_pointer()`와 `_append_runtime_event()`만 exporter로 분리하는 것이었습니다.

## 핵심 변경
- `watcher_runtime_exporter.py`를 추가해 `WatcherRuntimeExporter` dataclass와 `_watcher_repo_relative()` helper를 만들었습니다.
- `WatcherRuntimeExporter`는 `enabled`, run 경로, `current_run_path`, `repo_root`를 주입받아 `current_run.json`과 `events.jsonl` 기록을 담당합니다.
- runtime event sequence는 WatcherCore의 `_runtime_event_seq`에서 exporter의 `_event_seq`로 이전했습니다.
- `watcher_core.py`는 `self._exporter`를 초기화하고 `_write_current_run_pointer()`, `_append_runtime_event()`를 위임으로 교체했습니다.
- `_write_runtime_status()`는 이번 범위 밖으로 유지했습니다.
- `tests/test_watcher_runtime_exporter.py`를 추가해 pointer payload, event `seq` 증가, disabled exporter no-write 동작을 독립 검증했습니다.

## 검증
- 통과: `python3 -m py_compile watcher_core.py watcher_runtime_exporter.py tests/test_watcher_runtime_exporter.py`
  - 결과: PASS, 출력 없음.
- 통과: `python3 -m py_compile watcher_core.py watcher_runtime_exporter.py`
  - 결과: PASS, 출력 없음.
- 통과: `python3 -m unittest tests.test_watcher_runtime_exporter -v`
  - 결과: `Ran 3 tests in 0.005s`, `OK`.
- 통과: `python3 -m unittest tests.test_watcher_core -v 2>&1 | tail -5`
  - 결과: `Ran 264 tests in 9.550s`, `OK`.
- 통과: `python3 -c "from watcher_runtime_exporter import WatcherRuntimeExporter; print('import OK')"`
  - 결과: `import OK`.
- 통과: `git diff --check -- watcher_core.py watcher_runtime_exporter.py`
  - 결과: PASS, 출력 없음.
- 통과: `git diff --check -- watcher_core.py watcher_runtime_exporter.py tests/test_watcher_runtime_exporter.py`
  - 결과: PASS, 출력 없음.

## 남은 리스크
- 이번 slice는 runtime export 기록 로직의 위치를 바꾸는 내부 리팩터링입니다. live watcher/tmux runtime 검증은 실행하지 않았습니다.
- `watcher_core.py`는 이전 helper extraction, control signal extraction, job state extraction, artifact scanner extraction 변경이 이미 남아 있는 dirty 파일입니다. 이번 slice에서는 WatcherRuntimeExporter 초기화와 runtime export wrapper만 추가로 변경했습니다.
- `_write_runtime_status()`와 lane status builder는 turn state 의존이 많아 이번 범위에서 제외했습니다.
- product docs, agent/skill config, `.pipeline` control slot은 변경하지 않았습니다.
- commit, push, branch/PR publication, PR creation, merge, release, publication은 실행하지 않았습니다.
