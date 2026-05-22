# 2026-05-21 watcher core module helper extraction

## 변경 파일
- `watcher_core.py`
- `watcher_prompt_assembly.py`
- `pipeline_runtime/lane_surface.py`
- `tests/test_watcher_core.py`
- `work/5/21/2026-05-21-watcher-core-module-helper-extraction.md`

## 사용 skill
- `security-gate`: prompt temp file 쓰기/cleanup 유틸 이동이 파일 쓰기 경계와 cleanup 동작을 바꾸지 않는지 확인하기 위해 사용했습니다.
- `finalize-lite`: 실행한 검증, 미실행 범위, 문서 동기화 필요 여부, `/work` closeout 필요 여부를 정리하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- `watcher_core.py`에 남아 있던 모듈 레벨 유틸 일부가 lane surface 감지와 prompt assembly 책임에 섞여 있었습니다.
- WatcherCore 클래스 본문은 유지하면서, 함수 소유 위치를 기존 목적별 모듈로 옮기는 것이 이번 slice의 목적이었습니다.
- `_session_name_for_project()`는 이미 `pipeline_gui.project._session_name_for`가 같은 역할을 하므로 local duplicate를 제거할 수 있었습니다.

## 핵심 변경
- `pipeline_runtime/lane_surface.py`에 `_line_looks_like_input_prompt()`와 `_pane_text_has_gemini_ready_prompt()` compatibility helper를 추가하고 기존 공개 helper에 위임했습니다.
- `watcher_prompt_assembly.py`로 `_prompt_cleanup_list`, `_cleanup_prompt_files()`, `_write_prompt_file()`, `_normalize_prompt_text()`를 이동했습니다.
- `watcher_core.py`에서는 위 helper들의 local 정의와 `atexit`/`tempfile` import를 제거하고, 새 소유 모듈에서 import하도록 바꿨습니다.
- `watcher_core.py`의 `_session_name_for_project()` local 정의와 `_SESSION_PREFIX`를 제거하고 `pipeline_gui.project._session_name_for`를 alias import했습니다.
- `tests/test_watcher_core.py`에 이동된 lane surface helper와 prompt helper import/동작 회귀 테스트를 추가했습니다.
- WatcherCore 클래스 내부 메서드는 수정하지 않았습니다.

## 검증
- 통과: `python3 -m py_compile watcher_core.py watcher_prompt_assembly.py pipeline_runtime/lane_surface.py`
  - 결과: PASS, 출력 없음.
- 통과: `python3 -m unittest tests.test_watcher_core.PanePromptDetectionTest.test_moved_lane_surface_helpers_remain_available tests.test_watcher_core.PanePromptDetectionTest.test_moved_prompt_helpers_remain_available -v`
  - 결과: `Ran 2 tests in 0.002s`, `OK`.
- 통과: `python3 -m unittest tests.test_watcher_core -v 2>&1 | tail -5`
  - 결과: `Ran 264 tests in 10.530s`, `OK`.
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor -v 2>&1 | tail -5`
  - 결과: `Ran 221 tests in 2.450s`, `OK`.
- 통과: `python3 -c "... from watcher_prompt_assembly import _write_prompt_file, _normalize_prompt_text ... from pipeline_runtime.lane_surface import _pane_text_has_gemini_ready_prompt ..."`
  - 결과: `import OK`.
- 통과: `git diff --check -- watcher_core.py watcher_prompt_assembly.py pipeline_runtime/lane_surface.py`
  - 결과: PASS, 출력 없음.

## 남은 리스크
- 이번 slice의 `watcher_core.py` diff는 `+7/-75`로, net 기준 약 68줄 감소입니다. 요청의 "~150줄" 목표까지 더 줄이려면 추가 모듈 레벨 helper 추출이 필요하지만, `_pane_has_input_cursor` 이동은 이번 범위 밖이라 남겼습니다.
- `tests/test_watcher_core.py`에는 이전 slice에서 추가된 uncommitted 테스트도 같은 파일 diff에 함께 남아 있습니다. 이번 slice에서 새로 추가한 테스트는 moved helper import/동작 테스트입니다.
- 전체 repo unittest discover, browser/E2E, live runtime/tmux 검증은 실행하지 않았습니다.
- 현재 worktree에는 이전 Claude print JSONL lane integration, turn arbitration, schema/role harness, lane catalog 관련 수정/기록 파일이 남아 있습니다. 이번 slice에서는 관련 없는 기존 변경을 되돌리거나 포함하지 않았습니다.
- commit, push, branch/PR publication, PR creation, merge, release, publication은 실행하지 않았습니다.
