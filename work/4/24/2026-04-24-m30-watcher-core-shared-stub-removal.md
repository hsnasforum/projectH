# 2026-04-24 watcher_core shared stub removal

## 변경 파일
- `watcher_core.py`
- `work/4/24/2026-04-24-m30-watcher-core-shared-stub-removal.md`

## 사용 skill
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` `CONTROL_SEQ: 136`은 `watcher_core.py` 안에서 `pipeline_runtime.lane_surface`로 단순 위임만 하던 module-level stub 함수 7개를 제거하고 내부 호출을 `_shared_*` helper로 바꾸라고 지정했습니다.
- 이 slice는 행동 변경 없이 watcher thin client가 lane surface runtime truth를 직접 읽도록 중복 위임층을 줄이는 구조 정리입니다.

## 핵심 변경
- `_capture_pane_text`, `wait_for_pane_settle`, `_pane_text_has_busy_indicator`, `_pane_text_has_input_cursor`, `_pane_text_is_idle`, `_pane_text_has_codex_activity`, `_pane_text_has_gemini_activity`의 기존 `def` stub을 제거했습니다.
- `watcher_core.py` 내부 호출부를 `_shared_capture_pane_text`, `_shared_wait_for_pane_settle`, `_shared_pane_text_*` 이름으로 교체했습니다.
- `WatcherDispatchQueue`와 `StateMachine`에 넘기던 단순 lambda wrapper를 직접 `_shared_*` callable 참조로 바꿨습니다.
- `_line_looks_like_input_prompt`, `_pane_text_has_gemini_ready_prompt`, `_pane_has_input_cursor`, `_pane_has_working_indicator`는 보존했고, 보존 함수 내부 capture/check 호출만 shared helper로 바꿨습니다.
- 기존 `tests/test_watcher_core.py`가 legacy 이름을 mock patch 대상으로 계속 사용하므로, 함수 stub은 되살리지 않고 legacy patch target만 `_shared_*` 호출에 반영되는 작은 호환 callable로 연결했습니다.

## 검증
- `sha256sum .pipeline/implement_handoff.md`
  - `04b174595c4821eda8d393577e7676fc09ab11c8a706ae33d6365fb302b855c0` 일치 확인
- `python3 -m py_compile watcher_core.py`
  - 통과: 출력 없음
- `python3 -m unittest tests/test_watcher_core.py -v 2>&1 | tail -5`
  - 1차 실패: `AttributeError: watcher_core does not have the attribute '_capture_pane_text'` 계열 68 errors
  - 원인: 테스트가 삭제 대상 stub 이름을 patch target으로 직접 사용
  - 호환 callable 추가 후 통과: `Ran 202 tests in 6.628s`, `OK`
- `rg --pcre2 -n "def (_capture_pane_text|wait_for_pane_settle|_pane_text_has_busy_indicator|_pane_text_has_input_cursor|_pane_text_is_idle|_pane_text_has_codex_activity|_pane_text_has_gemini_activity)\b|(?<!_shared)_capture_pane_text\(|(?<!_shared_)wait_for_pane_settle\(|(?<!_shared)_pane_text_has_busy_indicator\(|(?<!_shared)_pane_text_has_input_cursor\(|(?<!_shared)_pane_text_is_idle\(|(?<!_shared)_pane_text_has_codex_activity\(|(?<!_shared)_pane_text_has_gemini_activity\(" watcher_core.py`
  - 통과: 매치 없음
- `git diff --check -- watcher_core.py work/4/24/2026-04-24-m30-watcher-core-shared-stub-removal.md`
  - 통과: 출력 없음

## 남은 리스크
- legacy mock patch target 호환 callable은 기존 테스트 계약을 유지하기 위한 과도기 표면입니다. 추후 테스트가 `_shared_*` 또는 `pipeline_runtime.lane_surface` owner를 직접 patch하도록 정리되면 제거할 수 있습니다.
- 다른 작업자가 만든 기존 dirty/untracked 파일은 그대로 두었고, 이번 slice에서는 `watcher_core.py`와 이 closeout만 변경했습니다.
